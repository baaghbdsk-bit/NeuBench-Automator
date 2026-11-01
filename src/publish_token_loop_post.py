import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
PERSON_URN = "urn:li:person:kCeVKYd195"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-Restli-Protocol-Version": "2.0.0",
    "LinkedIn-Version": "202401"
}

def publish_video_post(video_path: str):
    print(f"Preparing to upload {video_path}...")
    file_size = os.path.getsize(video_path)
    
    # 1. Register Upload for Video
    reg_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
            "owner": PERSON_URN,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
    
    r = requests.post(reg_url, headers=HEADERS, json=payload)
    if r.status_code not in (200, 201):
        print(f"Failed to register video upload: {r.status_code} - {r.text}")
        return False
        
    res_data = r.json()
    upload_url = res_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
    asset_urn = res_data['value']['asset']
    print(f"Asset registered: {asset_urn}")
    
    # 2. Upload file bytes
    with open(video_path, "rb") as f:
        video_bytes = f.read()
        
    upload_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "video/mp4"
    }
    up_res = requests.put(upload_url, headers=upload_headers, data=video_bytes)
    print(f"Upload status: {up_res.status_code}")
    if up_res.status_code not in (200, 201):
        print(f"Binary upload failed: {up_res.text}")
        return False

    # 3. Create UGC Post
    post_text = (
        "How do Large Language Models actually 'read' your prompt?\n\n"
        "Most people assume LLMs ingest text words directly. But internally, deep learning architectures only understand floating-point mathematics.\n\n"
        "Here is the exact 3-step pipeline behind every query:\n\n"
        "1. Byte-Pair Encoding (BPE) & Subword Splitting\n"
        "The model splits raw character strings into subword tokens. Common words stay whole ('high'), while complex or rare terms get decomposed ('latency' -> ['lat', 'ency']). Each token maps to an integer in a fixed vocabulary (e.g., Tiktoken cl100k_base).\n\n"
        "2. Embedding Lookup (High-Dimensional Projections)\n"
        "Token integers pass through an embedding lookup table, mapping each token ID to a dense vector in 4,096 dimensions. Position embeddings are added so the network remembers token sequence order.\n\n"
        "3. Multi-Head Self-Attention\n"
        "Vectors enter the transformer blocks where Q, K, and V matrix multiplications calculate contextual relationships before predicting the next token.\n\n"
        "Understanding this tokenization stage is critical for prompt caching, token reduction, and optimizing time-to-first-token (TTFT) in real-time agentic workflows.\n\n"
        "What tokenization quirk or prompt optimization technique have you encountered in production?\n\n"
        "#ArtificialIntelligence #MachineLearning #LLMOps #DeepLearning #GenerativeAI #SoftwareEngineering #Python"
    )

    ugc_url = "https://api.linkedin.com/v2/ugcPosts"
    ugc_payload = {
        "author": PERSON_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text
                },
                "shareMediaCategory": "VIDEO",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "How LLMs convert prompts to tokens and embedding vectors"
                        },
                        "media": asset_urn,
                        "title": {
                            "text": "How LLMs Process Your Prompt: Tokens to Vectors"
                        }
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    post_res = requests.post(ugc_url, headers=HEADERS, json=ugc_payload)
    print(f"Post response code: {post_res.status_code}")
    if post_res.status_code in (200, 201):
        post_urn = post_res.json().get("id")
        print(f"Successfully published video post! URN: {post_urn}")
        print(f"Live Link: https://www.linkedin.com/feed/update/{post_urn}/")
        return True
    else:
        print(f"Failed to publish UGC post: {post_res.text}")
        return False

if __name__ == "__main__":
    publish_video_post("how_llms_convert_prompt.mp4")
