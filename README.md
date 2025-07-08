# Stealth
=======

Stealth is a tool for getting different information about a product.

## Dockerized Setup and Testing Instructions

This project can be easily set up and tested using Docker and Docker Compose to ensure a consistent environment and prevent dependency issues.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

*   **Docker Desktop:** [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

### Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd stealth
    ```

2.  **Create a `.env` file:**
    Create a file named `.env` in the root directory of the project and add your SerpApi key:

    ```
    SERP_API_KEY=your_serp_api_key_here
    ```
    Replace `your_serp_api_key_here` with your actual SerpApi key. You can obtain one from [https://serpapi.com/](https://serpapi.com/).

3.  **Build the Docker images:**
    Navigate to the root directory of the project (where `docker-compose.yml` is located) and run:

    ```bash
    docker-compose build
    ```
    This command will build the Docker image for the application based on the `Dockerfile`.

### Running the Application

To start the application, run:

```bash
docker-compose up
```

This will start the FastAPI application, which will be accessible at `http://localhost:8000`.

### Testing the Application

Once the application is running (after `docker-compose up`), you can test the `/search` endpoint.

**Example API Call:**

You can use `curl` or any API client (like Postman or Insomnia) to test the endpoint.

```bash
curl "http://localhost:8000/search?q=apple%20iphone&location=us"
```

Replace `apple%20iphone` with your desired search query and `us` with the desired country code.

**Expected Output:**

The API will return a JSON array of shopping results, sorted by price.

```json
[
  {
    "title": "...",
    "price": "...",
    "price_string": "...",
    "product_link": "...",
    "currency": "...",
    "rating": "...",
    "reviews": "...",
    "snippet": "...",
    "source": "...",
    "source_icon": "...",
    "thumbnail": "...",
    "thumbnails": [],
    "delivery": "...",
    "second_hand_condition": "...",
    "position": "...",
    "product_id": "..."
  }
]
```

### Stopping the Application

To stop the running Docker containers, press `Ctrl+C` in the terminal where `docker-compose up` is running. If you want to stop and remove the containers, networks, and volumes, run:

```bash
docker-compose down
```
