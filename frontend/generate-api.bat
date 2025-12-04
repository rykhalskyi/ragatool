@echo off

:: Download the Swagger JSON file
curl -k http://localhost:8000/openapi.json -o openapi.json
echo openapi JSON file has been saved as openapi.json

:: Generate the TypeScript client
openapi --input openapi.json --output ./src/app/client
