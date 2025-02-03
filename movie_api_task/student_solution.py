from flask import Flask, abort, request, jsonify
import elasticsearch as ES

# from validate import validate_args

app = Flask(__name__)


@app.route("/")
def index():
    return "worked"


@app.route("/api/movies/")
def movie_list():
    # validate = validate_args(request.args)
    #
    # if not validate['success']:
    #     return abort(422)

    defaults = {
        "limit": 50,
        "page": 1,
        "sort": "id",
        "sort_order": "asc"
    }

    # Тут уже валидно все
    for param in request.args.keys():
        defaults[param] = request.args.get(param)

    # Уходит в тело запроса. Если запрос не пустой - мультисерч, если пустой - выдает все фильмы
    body = {
        "query": {
            "multi_match": {
                "query": defaults["search"],
                "fields": ["title", "description", "genre", "actors_names", "writers_names", "director"]
            }
        }
    } if defaults.get("search", False) else {}

    body["_source"] = dict()
    body["_source"]["includes"] = ["title", "description", "genre", "actors_names", "writers_names", "director"]

    params = {
        # '_source': ['id', 'title', 'imdb_rating'],
        "from": int(defaults["limit"]) * (int(defaults["page"]) - 1),
        "size": defaults["limit"],
        "sort": [
            {
                defaults["sort"]: defaults["sort_order"]
            }
        ]
    }

    es_client = ES.Elasticsearch([{"host": "192.168.11.128", "port": 9200}], )
    search_res = es_client.search(
        body=body,
        index="movies",
        params=params,
        filter_path=["hits.hits._source"]
    )
    es_client.close()

    return jsonify([doc["_source"] for doc in search_res["hits"]["hits"]])


@app.route("/api/movies/<string:movie_id>")
def get_movie(movie_id):
    es_client = ES.Elasticsearch([{"host": "192.168.11.128", "port": 9200}], )

    try:
        if not es_client.ping():
            return jsonify({"error":"oh("}), 500

        search_result = es_client.get(index="movies", id=movie_id, ignore=404)

        if search_result and search_result.get("found", False):
            return jsonify(search_result["_source"])

        return jsonify({"error": "Movie not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        es_client.close()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)