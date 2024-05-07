from flask import Flask, render_template, request, redirect
from bs4 import BeautifulSoup
import csv
import requests
import os

app = Flask(__name__)

def scrape_google(question):
    url = f"https://www.google.com/search?q={question}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def extract_question_answer_boxes(soup):
    question_boxes = soup.find_all("div", class_="BNeawe vvjwJb AP7Wnd")
    answer_boxes = soup.find_all("div", class_="BNeawe s3v9rd AP7Wnd")
    question_answer_pairs = []
    for question_box, answer_box in zip(question_boxes, answer_boxes):
        question = question_box.get_text()
        answer = answer_box.get_text()
        question_answer_pairs.append((question, answer))
    return question_answer_pairs

def filter_results(question_answer_pairs, whitelist, blacklist):
    filtered_pairs = []
    for pair in question_answer_pairs:
        question, _ = pair
        domain = question.split(" - ")[-1]  # 
        if domain in blacklist:
            continue
        elif domain in whitelist:
            filtered_pairs.append(pair)
        else:
            filtered_pairs.append(pair)
    return filtered_pairs[:5]  

def read_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

def save_to_csv(filtered_pairs):
    with open("question_answers.csv", 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Question", "Answer"])
        for pair in filtered_pairs:
            writer.writerow(pair)

def log_ip(ip):
    with open('visitors.log', 'a') as f:
        f.write(ip + '\n')

def is_blacklisted(ip_address):
    with open('blacklisted_ips.txt', 'r') as f:
        blacklist = f.read().splitlines()
    if ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()
    return ip_address in blacklist

@app.before_request
def block_blocked_ips():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if is_blacklisted(ip):
        return render_template('403.html'), 403

@app.route('/', methods=['GET', 'POST'])
def index():
    pairs = None
    if request.method == 'POST':
        user_question = request.form['question']
        search_results = scrape_google(user_question)
        question_answer_pairs = extract_question_answer_boxes(search_results)

        blacklist = read_file("blacklist.txt")
        whitelist = read_file("whitelist.txt")

        filtered_pairs = filter_results(question_answer_pairs, whitelist, blacklist)

        save_to_csv(filtered_pairs)
        pairs = filtered_pairs

    log_ip(request.headers.get('X-Forwarded-For', request.remote_addr))

    return render_template('index.html', pairs=pairs)

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

if __name__ == "__main__":
    app.run(debug=True)
