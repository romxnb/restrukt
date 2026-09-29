# Команда

Внутрішній застосунок компанії: профіль працівника, склад команди, державні свята.

- `backend/` — Symfony 7.4, Doctrine ORM (SQLite), JSON API під `/api`.
- `frontend/` — Vue 3 + TypeScript + Vite, сторінки в `src/pages/`, запити до API в `src/api/`.

Вхід демонстраційний: клієнт передає номер працівника в заголовку `X-Employee-Id`, сторінка `/login` дає обрати працівника.

## Запуск

```sh
cd backend
php bin/console doctrine:migrations:migrate -n
php bin/console app:seed-demo
php -S 127.0.0.1:8000 -t public

cd frontend
npm run dev
```

## Перевірки

```sh
cd backend
php bin/phpunit
vendor/bin/psalm
vendor/bin/php-cs-fixer fix --dry-run --diff

cd frontend
npm test
npm run typecheck
npm run lint
npm run format:check
```
