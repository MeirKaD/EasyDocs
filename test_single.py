# test_generate_response.py
import asyncio
from src.nodes import generate_response

async def test_generate_response():
    state = {
        "query": "How to send a POST Request to Bright Data's Web Scraper API",
        "platform": "bright_data",
        "operation_type": "POST",
        "action_plan": [
            "Navigate to Bright Data's Web Scraper API documentation page.",
            "Search for 'POST request' in the documentation.",
            "Locate the section detailing how to send a POST request.",
            "Identify the API endpoint URL for sending a POST request.",
            "Check for required parameters and headers for the POST request.",
            "Find authentication requirements for the POST request.",
            "Look for code examples or CURL commands demonstrating how to send a POST request.",
            "Extract and save the API endpoint URL, required parameters, headers, authentication details, and code examples.",
            "Summarize the information needed to send a POST request to Bright Data's Web Scraper API.",
            "Return the summarized information."
        ],
        "current_step": 0,
        "confidence": 0.8,
        "estimated_duration": 90,
        "complexity_level": "medium",
        "error": None,
        
        "confidence_level": 9,
        "explanation": "The documentation provides a comprehensive guide on sending POST requests to Bright Data's Web Scraper API. It includes the API endpoint URL, HTTP method, required headers, request body structure for different scraper types (PDP and Discovery), required and optional parameters, authentication details, and a cURL example. The information is accurate, relevant, and well-organized, making it easy to understand and implement. The inclusion of examples for both PDP and Discovery scrapers enhances its practical value.",
        "extracted_content": '''Based on the scraped documentation, here's how to send a POST request to Bright Data's Web Scraper API:

**API Endpoint URL:**

```
https://api.brightdata.com/datasets/v3/trigger
```

**HTTP Method:**

```
POST
```

**Required Headers:**

*   `Authorization`:  `Bearer <token>`, where `<token>` is your API key. You can find/generate the API key in your Bright Data account settings.
*   `Content-Type`: `application/json` (if sending the request body as JSON)

**Request Body:**

The request body should be a JSON array of inputs. The structure of the input depends on the type of web scraper you are using (PDP or Discovery).

*   **PDP Scrapers:** Require URLs as input. Example:

    ```json
    [{"url":"https://www.airbnb.com/rooms/50122531"}]
    ```

*   **Discovery Scrapers:**  The input can vary according to the specific scraper. Examples include keywords, search settings, or locations. Example:

    ```json
    [{"keyword": "light bulb"}, {"keyword": "dog toys"}, {"keyword": "home decor"}]
    ```

**Required Parameters:**

*   `dataset_id`:  The ID of the dataset for which you are triggering data collection. This is a query parameter in the URL. Example: `gd_l1vikfnt1wgvvqz95w`

**Optional Parameters (Query Parameters):**

*   `custom_output_fields`: List of output columns, separated by `|` (e.g., `url|about.updated_on`).
*   `type`: Set to `"discover_new"` to trigger a collection that includes a discovery phase.
*   `discover_by`: Specifies which discovery method to use (e.g., "keyword", "best_sellers_url", "category_url", "location").
*   `include_errors`:  Include errors report with the results.
*   `limit_per_input`: Limit the number of results per input.
*   `limit_multiple_results`: Limit the total number of results.
*   `notify`: URL where a notification will be sent once the collection is finished.
*   `endpoint`: Webhook URL where data will be delivered.
*   `format`: Specifies the format of the data to be delivered to the webhook endpoint (`json`, `ndjson`, `jsonl`, `csv`).
*   `auth_header`: Authorization header to be used when sending notification to notify URL or delivering data via webhook endpoint.
*   `uncompressed_webhook`:  Pass `true` to send the data uncompressed to the webhook.

**Authentication:**

Authentication is done via an API key. You need to include the `Authorization` header with the `Bearer` scheme and your API key.

**Example CURL Command:**

```
curl --request POST \
  --url https://api.brightdata.com/datasets/v3/trigger?dataset_id=YOUR_DATASET_ID \
  --header 'Authorization: Bearer YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data '[{"url": "https://il.linkedin.com/company/bright-data"}]'
```

Replace `YOUR_API_KEY` with your actual Bright Data API key and `YOUR_DATASET_ID` with your dataset ID.''',
        "final_response": ""  # This will be populated by generate_response
    }
    
    result = await generate_response(state)
    print("Generated Response:")
    print("=" * 50)
    print(result["final_response"])
    print("=" * 50)
    
    if "error" in result:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_generate_response())