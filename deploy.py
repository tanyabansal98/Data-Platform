import os, sys, shutil, zipfile, subprocess
import boto3

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
FUNC = "file-mover"
lam = boto3.client("lambda", region_name=REGION)

def zip_dir(src, out):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src):
            for f in files:
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, src))

os.makedirs("build", exist_ok=True)

# Layer (only if requirements.txt has content)
layer_arn = None
if os.path.getsize("requirements.txt") > 0:
    shutil.rmtree("build/layer", ignore_errors=True)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
        "-t", "build/layer/python",
        "--platform", "manylinux2014_x86_64", "--only-binary=:all:",
        "--python-version", "3.12", "--implementation", "cp"])
    zip_dir("build/layer", "build/layer.zip")
    with open("build/layer.zip", "rb") as f:
        layer_arn = lam.publish_layer_version(
            LayerName="file-mover-deps", Content={"ZipFile": f.read()},
            CompatibleRuntimes=["python3.12"])["LayerVersionArn"]

# Function
zip_dir("src", "build/function.zip")
with open("build/function.zip", "rb") as f:
    code = f.read()
layers = [layer_arn] if layer_arn else []
env = {"Variables": {"BUCKET_NAME": os.environ["BUCKET_NAME"]}}

try:
    lam.get_function(FunctionName=FUNC)
    exists = True
except lam.exceptions.ResourceNotFoundException:
    exists = False

if not exists:
    lam.create_function(
        FunctionName=FUNC, Runtime="python3.12",
        Role=os.environ["LAMBDA_ROLE_ARN"],
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": code}, Environment=env,
        Layers=layers, Timeout=30)
else:
    lam.update_function_code(FunctionName=FUNC, ZipFile=code)
    lam.get_waiter("function_updated").wait(FunctionName=FUNC)
    lam.update_function_configuration(
        FunctionName=FUNC, Environment=env, Layers=layers)
print("Deployed", FUNC)