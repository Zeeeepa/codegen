# Hello World Modal Example

This is a simple example that demonstrates how to deploy a basic Modal application that integrates with Codegen.

## Features

- Basic Modal function deployment
- Web endpoint for API access
- Scheduled function that runs every hour
- Integration with Codegen SDK

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10+
- [Modal CLI](https://modal.com/docs/guide/cli-reference)
- [Codegen SDK](https://docs.codegen.com)

## Setup

1. Install the required dependencies:

```bash
pip install modal codegen==0.52.19
```

2. Authenticate with Modal:

```bash
modal token new
```

## Deployment

You can deploy this example to Modal using the provided deploy script:

```bash
./deploy.sh
```

This will deploy the application to Modal and provide you with a URL to access the web endpoint.

## Usage

Once deployed, you can use the web endpoint to say hello:

```bash
curl "https://hello-world--web-hello.modal.run?name=YourName"
```

Replace `YourName` with your name to get a personalized greeting.

## API Response

The web endpoint returns a JSON response with the following structure:

```json
{
  "message": "Hello, YourName!"
}
```

## Components

This example includes three main components:

1. **Regular Function**: `hello()` - A simple function that returns a greeting
2. **Web Endpoint**: `web_hello()` - A web endpoint that returns a JSON greeting
3. **Scheduled Function**: `scheduled_hello()` - A function that runs every hour

## Local Testing

You can test the application locally before deploying:

```bash
python app.py
```

This will run the application locally and call the `hello()` function with the argument "Modal".

## Customization

You can customize this example by:

1. Adding more functions to the Modal app
2. Changing the schedule for the scheduled function
3. Adding more complex logic to the functions
4. Integrating with other Codegen features

## Troubleshooting

If you encounter issues:

1. Ensure you have the correct version of Modal and Codegen installed
2. Check that you're authenticated with Modal
3. Verify that the Modal CLI is installed correctly
4. Check the Modal logs for detailed error information

