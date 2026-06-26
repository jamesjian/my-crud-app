FROM python:3.11-slim

#Prevents Python from writing .pyc files to disk.
ENV PYTHONDONTWRITEBYTECODE=1
#Forces Python to flush outputs straight to the terminal log instantly (essential for viewing errors in GitHub Actions or server logs without delays).
ENV PYTHONUNBUFFERED=1
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./main.py /code/main.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
