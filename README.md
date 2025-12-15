# VML Ugly Sweater Teams Background Generator

## Purpose
- Interactive web app for generating custom Christmas sweater-themed Microsoft Teams backgrounds.
- Users select color themes, knit styles, and visual elements to personalize their Teams background.
- Built with Flask, featuring a festive playful design inspired by holiday sweaters.

## Setup (As Is)
- Create and activate a Python 3.9+ virtual environment.
- Install dependencies: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and add: `SECRET_KEY`, `BASIC_AUTH_USERNAME`, `BASIC_AUTH_PASSWORD`.
- Run the server: `python app.py` (listens on `http://localhost:8080`).

## Setup (Docker)
- Build the image: `docker build -t uglysweater .`.
- Provide the env vars via `docker run --env-file .env -p 8080:8081 uglysweater` (gunicorn listens on 8081 inside the container).
- Use the supplied `Dockerfile` with the reverse proxy defined under `nginx/` or adapt the `config/deploy.yml` Kamal stack.
- Alternatively run `docker-compose up --build` to launch the service with the mounted `.vault` volume.

## Usage Examples
- Landing page: view the playful hero section with festive typography.
- Selection: choose from Christmas or brand color themes, three knit styles (chunky, fair isle, tacky), and three visual element options (snowflakes, trees, brand elements).
- Generation: click the CTA button to generate and download your custom Teams background.
- Tutorial: follow the step-by-step guide to integrate the background into Microsoft Teams.
- Admin view: visit `/peekaboo` (basic auth protected) to inspect sessions, requests, and logs.
