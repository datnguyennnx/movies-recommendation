# LLM Application Boilerplate

This project provides a boilerplate for quickly setting up an LLM (Language Model) application with a Next.js frontend and a FastAPI backend. It uses Docker for containerization and includes a Makefile for easy deployment.

## Project Structure

-   `recommender-ui`: Next.js 14 frontend with shadcn UI library
-   `recommender-be`: Python FastAPI backend with WebSocket support
-   `docker-compose.yml`: Docker configuration for the entire stack
-   `Makefile`: Simplified commands for building and running the project

## Getting Started

### Prerequisites

-   Git
-   Docker
-   Docker Compose
-   Make (optional, but recommended)

### Cloning the Repository

To clone this project, run the following command:

```bash
git clone https://github.com/datnguyennnx/llm-app-boilerplate.git
cd llm-app-boilerplate
```

### Running the Project

We use a Makefile to simplify the Docker commands. Here are the available commands:

1. Build and start the entire stack:

    ```
    make up
    ```

2. Stop and remove the containers:
    ```
    make down
    ```

If you don't have Make installed, you can use the Docker Compose commands directly:

```bash
# Build and start the stack
docker-compose up -d

# Stop and remove the containers
docker-compose down
```

## Accessing the Application

Once the containers are up and running:

-   The frontend will be available at: `http://localhost:3000`
-   The backend API will be available at: `http://localhost:8000`

## Development

For development purposes, you can run each service individually. Refer to the README files in the `recommender-ui` and `recommender-be` directories for more detailed instructions on running and developing each component separately.

## Tracing with Langfuse

This project uses Langfuse for tracing LLM interactions. The tracing implementation helps in monitoring, debugging, and evaluating the LLM pipeline. Here's an overview of the tracing setup:

1. The `config/settings.py` file includes the Langfuse configuration variables.
2. Langfuse is initialized in the main application (`main.py`) and in relevant modules.
3. The `@observe()` decorator from Langfuse is used on key functions in `pipeline.py`, `metrics.py`, and `evaluator.py` to trace specific operations and evaluations.
4. Langfuse context is updated within `pipeline.py` to ensure proper tracing throughout the LLM interaction process.

To use Langfuse tracing:

1. Set up a Langfuse account and obtain your API keys.
2. Set the following environment variables in your `.env` file:
    - `LANGFUSE_PUBLIC_KEY`: Your Langfuse public key
    - `LANGFUSE_SECRET_KEY`: Your Langfuse secret key
    - `LANGFUSE_HOST`: Your Langfuse API endpoint (default is "https://cloud.langfuse.com")

These settings can be configured in the `.env` file or set as environment variables in your deployment environment.

## Customizing the Template

This boilerplate provides a starting point for your LLM application. You can customize the frontend and backend components to fit your specific use case. Some areas you might want to focus on:

1. Modify the frontend UI in the `recommender-ui` directory to match your application's needs.
2. Update the backend API in the `recommender-be` directory to integrate with your chosen LLM and implement your business logic.
3. Adjust the Docker and Makefile configurations if you need to add more services or change the existing setup.
4. Customize the tracing implementation to fit your specific monitoring and debugging needs.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
