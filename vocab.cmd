API_KEY="X-CKAN-API-Key: ${1}"

curl --location --request POST 'http://localhost:5000/api/action/vocabulary_create' \
--header "${API_KEY}" \
--data-raw '{
    "name": "project_tags",
    "tags": [
        {
            "name": "Algorithms"
        },
        {
            "name": "Bronx"
        },
        {
            "name": "Buildings"
        },
        {
            "name": "Dashboard"
        },
        {
            "name": "Hackathon"
        },
        {
            "name": "Health"
        },
        {
            "name": "Map"
        },
        {
            "name": "Python"
        }
    ]
}'


curl --location --request POST 'http://localhost:5000/api/action/vocabulary_create' \
--header "${API_KEY}" \
--data-raw '{
    "name": "project_category",
    "tags": [
        {
            "name": "Youth"
        },
        {
            "name": "Nonprofit"
        },
        {
            "name": "Academia"
        },
        {
            "name": "Data Journalism"
        },
        {
            "name": "Interesting Tech"
        },
        {
            "name": "Civic Advocate"
        },
        {
            "name": "Research Lab"
        },
        {
            "name": "Miscellaneous"
        }
    ]
}'


curl --location --request POST 'http://localhost:5000/api/action/vocabulary_create' \
--header "${API_KEY}" \
--data-raw '{
    "name": "app_category",
    "tags": [
        {
            "name": "Youth"
        },
        {
            "name": "Nonprofit"
        },
        {
            "name": "Academia"
        },
        {
            "name": "Data Journalism"
        },
        {
            "name": "Interesting Tech"
        },
        {
            "name": "Civic Advocate"
        },
        {
            "name": "Research Lab"
        },
        {
            "name": "Miscellaneous"
        }
    ]
}'
