#!/usr/bin/env bash
# Цикл Ральфа для restrukt: повторює режим `step` у новій сесії агента,
# поки в черзі плану є доступна частина. Стан живе у файлах проєкту.

set -u

plugin_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
plan="docs/restrukt/plan.md"
log_file="docs/restrukt/log.md"
stop_file="docs/restrukt/stop"
engine="claude"
max=12
commit=0
scope=""

usage() {
  cat <<'USAGE'
restrukt_loop.sh — одна частина плану за один запуск агента, повторно до кінця черги.

Використання: scripts/restrukt_loop.sh [параметри] [обсяг або назва частини]

  --max N                 межа кроків, типово 12; 0 — без межі
  --engine claude|codex   чим запускати крок, типово claude
  --plan ШЛЯХ             план, типово docs/restrukt/plan.md
  --log ШЛЯХ              журнал, типово docs/restrukt/log.md
  --stop-file ШЛЯХ        файл зупинки, типово docs/restrukt/stop
  --commit                коміт після кожного кроку зі змінами
  -h, --help              ця довідка

Змінні середовища:
  RESTRUKT_ENGINE_ARGS    аргументи запуску агента
                          (для claude типово --permission-mode acceptEdits)
  RESTRUKT_LOOP_LOG_DIR   тека для виводу кроків

Цикл зупиняється, коли доступних частин немає, вичерпано межу, з'явився файл
зупинки, крок завершився помилкою або два кроки поспіль нічого не змінили.
USAGE
}

need_value() {
  if [ -z "${2:-}" ]; then
    echo "Параметр $1 потребує значення" >&2
    exit 2
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --max) need_value "$1" "${2:-}"; max=$2; shift 2 ;;
    --engine) need_value "$1" "${2:-}"; engine=$2; shift 2 ;;
    --plan) need_value "$1" "${2:-}"; plan=$2; shift 2 ;;
    --log) need_value "$1" "${2:-}"; log_file=$2; shift 2 ;;
    --stop-file) need_value "$1" "${2:-}"; stop_file=$2; shift 2 ;;
    --commit) commit=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; scope="$*"; break ;;
    -*) echo "Невідомий параметр: $1" >&2; usage >&2; exit 2 ;;
    *) scope="${scope:+$scope }$1"; shift ;;
  esac
done

case "$engine" in
  claude|codex) ;;
  *) echo "Невідомий засіб запуску: $engine" >&2; exit 2 ;;
esac

if ! printf '%s' "$max" | grep -Eq '^[0-9]+$'; then
  echo "Межа кроків має бути цілим числом" >&2
  exit 2
fi

if ! command -v "$engine" >/dev/null 2>&1; then
  echo "Немає $engine у PATH: цикл не може запустити крок" >&2
  exit 3
fi

if [ ! -f "$plugin_root/skills/restrukt/SKILL.md" ]; then
  echo "Не знайдено skills/restrukt/SKILL.md у $plugin_root" >&2
  exit 3
fi

engine_args=${RESTRUKT_ENGINE_ARGS-}
if [ -z "$engine_args" ] && [ "$engine" = "claude" ]; then
  engine_args="--permission-mode acceptEdits"
fi

log_dir=${RESTRUKT_LOOP_LOG_DIR:-${TMPDIR:-/tmp}/restrukt-loop}
mkdir -p "$log_dir" || exit 3

prompt="Прочитай $plugin_root/skills/restrukt/SKILL.md і виконай режим \`step\` з аргументами: $scope"

# Стани черги з розділу «Частини»: готово, очікує, в роботі, заблоковано, нерозпізнане.
plan_counts() {
  [ -f "$plan" ] || { echo "0 0 0 0 0"; return; }
  awk '
    /^## / { inparts = (index($0, "Частини") > 0); next }
    !inparts { next }
    /^[[:space:]]*\|/ {
      n = split($0, cell, "|")
      state = ""
      name = ""
      for (i = 1; i <= n; i++) gsub(/^[ \t`*]+|[ \t`*]+$/, "", cell[i])
      for (i = n; i >= 1; i--) if (cell[i] != "") { state = cell[i]; break }
      for (i = 1; i <= n; i++) if (cell[i] != "") { name = cell[i]; break }
      if (state == "" || state == "Стан" || name == "Частина") next
      if (state ~ /^[-: ]+$/) next
      if (substr(state, 1, 1) == "<" || substr(name, 1, 1) == "<") next
      if (index(state, "заблоковано") > 0) { blocked++ }
      else if (index(state, "в роботі") > 0) { active++ }
      else if (index(state, "очікує") > 0) { waiting++ }
      else if (index(state, "готово") > 0) { done++ }
      else { other++ }
    }
    END { print done+0, waiting+0, active+0, blocked+0, other+0 }
  ' "$plan"
}

fingerprint() {
  {
    cat "$plan" "$log_file" 2>/dev/null
    git status --porcelain 2>/dev/null
  } | cksum
}

last_log_heading() {
  [ -f "$log_file" ] || return 1
  grep '^## ' "$log_file" 2>/dev/null | tail -1 | sed 's/^## //'
}

report_queue() {
  set -- $(plan_counts)
  echo "Черга: готово $1, очікує $2, в роботі $3, заблоковано $4, нерозпізнано $5"
}

echo "restrukt loop · $engine · межа ${max:-0} · план $plan"
[ -n "$scope" ] && echo "Аргумент кроку: $scope"
echo "Вивід кроків: $log_dir"
[ -f "$plan" ] && report_queue || echo "Плану ще немає: перший крок його підготує"

step=0
stale=0
reason="межу кроків вичерпано"

while [ "$max" -eq 0 ] || [ "$step" -lt "$max" ]; do
  if [ -e "$stop_file" ]; then
    reason="є файл зупинки $stop_file"
    break
  fi

  if [ -f "$plan" ]; then
    set -- $(plan_counts)
    if [ "$(($2 + $3))" -eq 0 ]; then
      if [ "$4" -gt 0 ]; then
        reason="доступних частин немає: заблоковано $4"
      elif [ "$5" -gt 0 ]; then
        reason="стани $5 рядків черги нерозпізнані: перевір розділ «Частини»"
      else
        reason="черга завершена"
      fi
      break
    fi
  fi

  step=$((step + 1))
  echo
  echo "── Крок $step ──"
  before=$(fingerprint)

  # Навмисне розбиття engine_args на слова.
  # shellcheck disable=SC2086
  if [ "$engine" = "claude" ]; then
    claude -p "$prompt" $engine_args 2>&1 | tee "$log_dir/step-$step.log"
  else
    codex exec "$prompt" $engine_args 2>&1 | tee "$log_dir/step-$step.log"
  fi
  status=${PIPESTATUS[0]}

  if [ "$status" -ne 0 ]; then
    reason="крок $step завершився помилкою запуску ($status)"
    break
  fi

  after=$(fingerprint)
  if [ "$before" = "$after" ]; then
    stale=$((stale + 1))
    echo "Крок $step нічого не змінив ($stale поспіль)"
  else
    stale=0
    if [ "$commit" -eq 1 ] && git rev-parse --git-dir >/dev/null 2>&1; then
      message=$(last_log_heading) || message=""
      [ -n "$message" ] || message="крок $step"
      git add -A && git commit -q -m "restrukt: $message" && echo "Коміт: restrukt: $message"
    fi
  fi

  [ -f "$plan" ] && report_queue

  if [ "$stale" -ge 2 ]; then
    reason="два кроки поспіль без змін"
    break
  fi
done

echo
echo "Зупинка після $step кроків: $reason"
[ -f "$plan" ] && report_queue
echo "Стан читай у $plan та $log_file"
