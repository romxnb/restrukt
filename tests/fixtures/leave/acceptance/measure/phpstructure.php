<?php
ini_set('display_errors', 'stderr');
// usage: php phpstructure.php <file>... — prints JSON: per class-like: kind, name, implements, methods with visibility, line counts and forwarding flag.
$result = [];
foreach (array_slice($argv, 1) as $file) {
    $tokens = token_get_all(file_get_contents($file));
    $count = count($tokens);
    $namespace = '';
    for ($i = 0; $i < $count; ++$i) {
        $token = $tokens[$i];
        if (!is_array($token)) {
            continue;
        }
        if (T_NAMESPACE === $token[0]) {
            $namespace = '';
            for ($j = $i + 1; $j < $count && ';' !== $tokens[$j] && '{' !== $tokens[$j]; ++$j) {
                if (is_array($tokens[$j]) && in_array($tokens[$j][0], [T_NAME_QUALIFIED, T_STRING], true)) {
                    $namespace .= $tokens[$j][1];
                }
            }
        }
        if (!in_array($token[0], [T_CLASS, T_INTERFACE, T_TRAIT, T_ENUM], true)) {
            continue;
        }
        // skip ::class and anonymous classes
        $prev = $i - 1;
        while ($prev >= 0 && is_array($tokens[$prev]) && T_WHITESPACE === $tokens[$prev][0]) {
            --$prev;
        }
        if ($prev >= 0 && is_array($tokens[$prev]) && in_array($tokens[$prev][0], [T_DOUBLE_COLON, T_NEW], true)) {
            continue;
        }
        $kind = [T_CLASS => 'class', T_INTERFACE => 'interface', T_TRAIT => 'trait', T_ENUM => 'enum'][$token[0]];
        $modifiers = [];
        for ($p = $prev; $p >= 0 && is_array($tokens[$p]) && in_array($tokens[$p][0], [T_ABSTRACT, T_FINAL, T_READONLY, T_WHITESPACE], true); --$p) {
            if (T_WHITESPACE !== $tokens[$p][0]) {
                $modifiers[] = strtolower($tokens[$p][1]);
            }
        }
        $j = $i + 1;
        while (!is_array($tokens[$j]) || T_STRING !== $tokens[$j][0]) {
            ++$j;
        }
        $name = $tokens[$j][1];
        $implements = [];
        $extends = [];
        $mode = null;
        for (; '{' !== $tokens[$j]; ++$j) {
            if (is_array($tokens[$j])) {
                if (T_IMPLEMENTS === $tokens[$j][0]) { $mode = 'implements'; continue; }
                if (T_EXTENDS === $tokens[$j][0]) { $mode = 'extends'; continue; }
                if (in_array($tokens[$j][0], [T_STRING, T_NAME_QUALIFIED, T_NAME_FULLY_QUALIFIED], true) && $mode) {
                    $short = substr(strrchr('\\'.$tokens[$j][1], '\\'), 1);
                    if ('implements' === $mode) { $implements[] = $short; } else { $extends[] = $short; }
                }
            }
        }
        $classStart = $token[2];
        $depth = 0;
        $methods = [];
        $properties = 0;
        $constants = 0;
        for ($k = $j; $k < $count; ++$k) {
            $t = $tokens[$k];
            if ('{' === $t || (is_array($t) && in_array($t[0], [T_CURLY_OPEN, T_DOLLAR_OPEN_CURLY_BRACES], true))) {
                ++$depth;
            } elseif ('}' === $t) {
                --$depth;
                if (0 === $depth) {
                    $classEnd = $k;
                    break;
                }
            } elseif (1 === $depth && is_array($t) && T_CONST === $t[0]) {
                ++$constants;
            } elseif (1 === $depth && is_array($t) && T_VARIABLE === $t[0]) {
                ++$properties;
            } elseif (1 === $depth && is_array($t) && T_FUNCTION === $t[0]) {
                $visibility = 'public';
                $static = false;
                for ($b = $k - 1; $b > 0 && (is_array($tokens[$b]) && in_array($tokens[$b][0], [T_PUBLIC, T_PROTECTED, T_PRIVATE, T_STATIC, T_ABSTRACT, T_FINAL, T_WHITESPACE, T_ATTRIBUTE, T_DOC_COMMENT, T_COMMENT], true)); --$b) {
                    if (in_array($tokens[$b][0], [T_PUBLIC, T_PROTECTED, T_PRIVATE], true)) { $visibility = strtolower($tokens[$b][1]); }
                    if (T_STATIC === $tokens[$b][0]) { $static = true; }
                }
                $m = $k + 1;
                while ($m < $count && ((is_array($tokens[$m]) && T_WHITESPACE === $tokens[$m][0]) || '&' === $tokens[$m])) { ++$m; }
                if ($m >= $count || '(' === $tokens[$m]) { continue; }
                $methodName = is_array($tokens[$m]) ? $tokens[$m][1] : $tokens[$m];
                $startLine = $t[2];
                // find body
                $parens = 0;
                for ($m2 = $m; $m2 < $count; ++$m2) {
                    if ('(' === $tokens[$m2]) { ++$parens; }
                    if (')' === $tokens[$m2]) { --$parens; }
                    if (0 === $parens && ('{' === $tokens[$m2] || ';' === $tokens[$m2])) { break; }
                }
                $bodyLines = 0;
                $statements = 0;
                $forwarding = false;
                $endLine = $startLine;
                if ('{' === $tokens[$m2]) {
                    $d = 0;
                    $bodyTokens = [];
                    for ($e = $m2; $e < $count; ++$e) {
                        $bt = $tokens[$e];
                        if ('{' === $bt || (is_array($bt) && in_array($bt[0], [T_CURLY_OPEN, T_DOLLAR_OPEN_CURLY_BRACES], true))) { ++$d; }
                        if ('}' === $bt) { --$d; if (0 === $d) { break; } }
                        if (is_array($bt)) { $endLine = $bt[2] + substr_count($bt[1], "\n"); }
                        if (';' === $bt && 1 === $d) { ++$statements; }
                        $bodyTokens[] = is_array($bt) ? $bt[1] : $bt;
                    }
                    $body = trim(implode('', array_slice($bodyTokens, 1)));
                    $forwarding = 1 === $statements && (bool) preg_match('/^(return\s+)?\$this->\w+->\w+\([^;]*\);$/s', $body) && '__construct' !== $methodName && !str_contains($body, ')->');
                    $bodyLines = max(0, $endLine - $startLine + 1);
                }
                $methods[] = ['name' => $methodName, 'visibility' => $visibility, 'static' => $static, 'lines' => $bodyLines, 'statements' => $statements, 'forwarding' => $forwarding];
                $k = $e ?? $m2;
                unset($e);
            }
        }
        $result[] = [
            'file' => $file, 'namespace' => $namespace, 'kind' => $kind, 'name' => $name, 'modifiers' => $modifiers,
            'implements' => $implements, 'extends' => $extends, 'methods' => $methods, 'properties' => $properties, 'constants' => $constants,
            'lines' => isset($classEnd) ? (is_array($tokens[$classEnd]) ? $tokens[$classEnd][2] : null) : null,
        ];
        $i = $classEnd ?? $i;
    }
}
echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), "\n";
