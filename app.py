from flask import Flask, render_template, jsonify
import requests
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

def fetch_contest_dates():
    url = "https://codeforces.com/api/contest.list"
    res = requests.get(url)
    res.raise_for_status()
    contests = res.json()["result"]

    return {
        c["id"]: datetime.utcfromtimestamp(c["startTimeSeconds"]).strftime("%d %b %Y")
        for c in contests if c["phase"] != "BEFORE"
    }

def fetch_latest_problems_by_rating():
    problems_url = "https://codeforces.com/api/problemset.problems"
    problems_res = requests.get(problems_url)
    problems_res.raise_for_status()
    problems = problems_res.json()["result"]["problems"]

    contest_dates = fetch_contest_dates()
    rating_bins = defaultdict(list)

    for prob in problems:
        rating = prob.get("rating")
        cid = prob.get("contestId")
        if rating is None or not (800 <= rating <= 2000) or rating % 100 != 0:
            continue
        if cid in contest_dates and "index" in prob:
            rating_bins[rating].append({
                "contestId": cid,
                "index": prob["index"],
                "name": prob["name"],
                "date": contest_dates[cid],
                "date_sort": datetime.strptime(contest_dates[cid], "%d %b %Y")
            })

    for rating in rating_bins:
        rating_bins[rating].sort(key=lambda x: x["date_sort"], reverse=True)
        for p in rating_bins[rating]:
            del p["date_sort"]
        rating_bins[rating] = rating_bins[rating][:25]  # Limit per rating

    return dict(sorted(rating_bins.items()))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/latest_problems")
def latest_problems():
    return jsonify(fetch_latest_problems_by_rating())

if __name__ == "__main__":
    app.run(debug=True)
