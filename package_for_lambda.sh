mkdir lambda_package
cp main.py lambda_package/lambda_function.py
cd lambda_package
uv pip install -r ../requirements.txt --target .
zip -r ../lambda_deploy.zip .