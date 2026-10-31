**Live demo:** <https://pulse-backend-hu93.onrender.com/api/posts/>

> Hosted on a free tier, so the first request after idle time can take up to a minute. Media uploads are disabled in the demo because the free host's disk isn't persistent.

# Pulse Backend

A social media REST API built with Django and Django REST Framework. Users can post text and media, follow each other, like, comment, and repost, and see a feed of posts from the people they follow.

## Features

- JWT authentication (register, login, token refresh)
- Posts with multiple image, video, or file uploads
- Likes (toggle), comments with nested replies, reposts (toggle)
- Follow and unfollow users, plus a personalised feed
- User profiles showing posts, replies, and likes
- Owner-only editing and deleting of posts and comments
- Paginated responses (10 per page)

## Tech stack

Python, Django 6, Django REST Framework, SimpleJWT, django-cors-headers, SQLite (PostgreSQL planned)

## Getting started

```bash
git clone https://github.com/kevneto1000/pulse-backend.git
cd pulse-backend
python -m venv env
source env/Scripts/activate      # Windows Git Bash; use env\Scripts\Activate.ps1 in PowerShell
pip install -r requirements.txt
cp .env.example .env             # then set a real SECRET_KEY
python manage.py migrate
python manage.py runserver
```

### Environment variables

| Name | Description |
| --- | --- |
| `SECRET_KEY` | Django secret key (generate a new one) |
| `DEBUG` | `True` for local development |

## API overview

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/users/register/` | Create an account |
| POST | `/api/auth/login/` | Get access and refresh tokens |
| POST | `/api/auth/refresh/` | Refresh the access token |
| GET | `/api/users/profile/<username>/` | Profile with posts, replies, likes |
| GET, POST | `/api/posts/` | List or create posts (multipart `media` for files) |
| GET, PATCH, DELETE | `/api/posts/<id>/` | Read, edit, or delete your own post |
| POST | `/api/posts/<id>/like/` | Toggle like |
| POST | `/api/posts/<id>/repost/` | Toggle repost |
| GET | `/api/posts/feed/` | Posts from people you follow |
| GET, POST | `/api/comments/?post=<id>` | List or add comments |
| PATCH, DELETE | `/api/comments/<id>/` | Edit or delete your own comment |
| POST | `/api/follows/toggle/` | Follow or unfollow (`{"user_id": 2}`) |

Authenticated requests use the header `Authorization: Bearer <access token>`.

## Design notes

- Likes and counts attach to the original post, so liking a repost counts as liking the original.
- Like, comment, and repost counts are computed with database subqueries to avoid N+1 queries.
- Unique constraints on likes and follows prevent duplicates, even with simultaneous requests.
- List endpoints are scoped per user so people can only modify their own data.

## Roadmap

- [ x ] Automated tests
- [ x ] Empty-post validation
- [ x ] Render and PostgreSQL
- [ ] Password strength validation and empty-post validation
- [ x ] Deployed demo

## Author

[Nduka Kevin] · [portfolio link: https://kevin-portfolio-mocha.vercel.app/] · [LinkedIn: https://www.linkedin.com/in/kevin-nduka-0901161b2/]
