from huggingface_hub import HfApi

api = HfApi()
repo_id = "FalconGlide/cve-severity-classifier"  # replace with your actual username

api.create_repo(repo_id, exist_ok=True)
api.upload_folder(
    folder_path="app/models/severity_classifier_final",
    repo_id=repo_id,
)
print(f"Model pushed to https://huggingface.co/{repo_id}")