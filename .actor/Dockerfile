# PDF Accessibility Basics Check (title2-pdf-census site_check). Apache-2.0.
# Built with the repository root as context (dockerContextDir "..").
FROM apify/actor-python:3.12

COPY requirements-actor.txt ./
RUN pip install --no-cache-dir -r requirements-actor.txt

COPY census.py site_check.py actor_main.py ./

CMD ["python3", "actor_main.py"]
