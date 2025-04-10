import os
import git
from git import Repo
import requests
from multiprocessing import Pool
import logging
import json
import base64
import sys
from urllib.parse import urlparse, urlunparse
import time
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Daha az verbose çıktı

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Yerel çalışma dizini.
WORKING_DIR = os.getenv("WORKING_DIR", "./repos")

# Kimlik bilgileri
BITBUCKET_WORKSPACE_ID = os.getenv("BITBUCKET_WORKSPACE_ID")
BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")
BITBUCKET_PAT = os.getenv("BITBUCKET_PAT")

# Azure DevOps kimlik bilgileri ve ayarları
AZURE_ORG = os.getenv("AZURE_ORG")
AZURE_PROJECT = os.getenv("AZURE_PROJECT")  # Azure Project ID
AZURE_PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")  # Azure Project Name
AZURE_PAT = os.getenv("AZURE_PAT")
AZURE_ENCODED_PAT = base64.b64encode(f":{AZURE_PAT}".encode()).decode()

AZURE_API_VERSION = "7.1"
AZURE_API_URL = f"https://dev.azure.com/{AZURE_ORG}/{AZURE_PROJECT}/_apis/git/repositories?api-version={AZURE_API_VERSION}"

AZURE_HEADERS = {
    "Authorization": f"Basic {AZURE_ENCODED_PAT}",
    "Content-Type": "application/json"
}

# Senkronizasyon geçmişini tutmak için dosya adı
SYNC_HISTORY_FILE = os.getenv("SYNC_HISTORY_FILE", "sync_history.json")

# Senkronizasyon geçmişini oku
def read_sync_history():
    if os.path.exists(SYNC_HISTORY_FILE):
        try:
            with open(SYNC_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Son senkronizasyon bilgilerini yaz
def write_sync_history(history):
    with open(SYNC_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

# Bitbucket API ile repoları alma
def get_bitbucket_repos():
    params = {'sort': '-updated_on'}
    url = f"https://api.bitbucket.org/2.0/repositories/{BITBUCKET_WORKSPACE_ID}"
    response = requests.get(url, params=params, auth=(BITBUCKET_USERNAME, BITBUCKET_PAT))
    repos = response.json()["values"]
    return [(repo["name"], repo["links"]["clone"][0]["href"], repo.get("updated_on", "")) for repo in repos]

def construct_bitbucket_url(original_url, username, password):
    parsed = urlparse(original_url)
    domain = parsed.netloc.split('@')[-1]
    new_netloc = f"{username}:{password}@{domain}"
    return urlunparse((parsed.scheme, new_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

# Azure Repos'ta repo var mı kontrol et ve yoksa oluştur
def ensure_azure_repo(repo_name):
    response = requests.get(AZURE_API_URL, headers=AZURE_HEADERS)
    if response.status_code != 200:
        logger.error(f"Azure Repos listesi alınamadı: {response.text}")
        return False

    try:
        data = response.json()
    except Exception as e:
        logger.error(f"JSON ayrıştırma hatası: {response.text}")
        return False

    repos = data.get("value", [])
    if any(repo["name"] == repo_name for repo in repos):
        logger.info(f"{repo_name} zaten Azure Repos'ta mevcut.")
        return True

    payload = {"name": repo_name, "project": {"id": AZURE_PROJECT}}
    create_response = requests.post(AZURE_API_URL, headers=AZURE_HEADERS, data=json.dumps(payload))

    if create_response.status_code == 201:
        logger.info(f"{repo_name} Azure Repos'ta oluşturuldu.")
        return True
    else:
        logger.error(f"{repo_name} oluşturulamadı: {create_response.text}")
        return False

# Azure repo URL'sini oluştur
def get_azure_repo_url(repo_name):
    return f"https://{AZURE_PAT}@dev.azure.com/{AZURE_ORG}/{AZURE_PROJECT_NAME}/_git/{repo_name}"

# Değişiklik olup olmadığını kontrol et
def has_changes(repo, branch_name, sync_history):
    try:
        repo_name = os.path.basename(repo.working_dir)
        
        # Bitbucket'tan en son değişiklikleri al
        origin = repo.remote("origin")
        origin.fetch()
        
        # Yerel branch'i güncelle
        if branch_name in repo.heads:
            local_branch = repo.heads[branch_name]
            local_branch.checkout()
            repo.git.pull("origin", branch_name)
        else:
            # Branch yoksa, yeni oluştur ve checkout yap
            repo.git.checkout('-b', branch_name, f'origin/{branch_name}')
        
        # Şu anki commit ID'sini al
        current_commit = repo.head.commit.hexsha
        
        # Senkronizasyon geçmişini kontrol et
        last_synced_commit = sync_history.get(repo_name, {}).get(branch_name, None)
        
        # Eğer daha önce senkronize edilmemişse veya commit değişmişse
        if last_synced_commit != current_commit:
            logger.info(f"{repo_name}:{branch_name} - Değişiklik tespit edildi.")
            return True, current_commit
        else:
            logger.info(f"{repo_name}:{branch_name} - Değişiklik yok.")
            return False, current_commit
    
    except Exception as e:
        logger.error(f"Değişiklik kontrolü sırasında hata: {e}")
        return True, None  # Hata durumunda değişiklik var sayıyoruz

# Senkronizasyon fonksiyonu (Tüm branch'ler)
def sync_repo(args):
    repo_name, bitbucket_clone_url, last_updated = args
    repo_dir = os.path.join(WORKING_DIR, repo_name)
    azure_url = get_azure_repo_url(repo_name)
    bitbucket_url = construct_bitbucket_url(bitbucket_clone_url, BITBUCKET_USERNAME, BITBUCKET_PAT)

    # Senkronizasyon geçmişini oku
    sync_history = read_sync_history()
    
    try:
        if not ensure_azure_repo(repo_name):
            return

        # Eğer repo yerel olarak yoksa klonla
        if not os.path.exists(repo_dir):
            logger.info(f"{repo_name} Bitbucket'tan klonlanıyor...")
            Repo.clone_from(bitbucket_url, repo_dir)
        else:
            logger.info(f"{repo_name} zaten var, güncelleniyor...")

        if not os.path.isdir(os.path.join(repo_dir, ".git")):
            logger.warning(f"{repo_name} klasörü bir git deposu değil, işlem atlanıyor.")
            return

        repo = Repo(repo_dir)
        origin = repo.remote("origin")
        origin.fetch()

        # Azure uzak repository'si değiştir veya ekle
        if "azure" in [r.name for r in repo.remotes]:
            # Uzak repo adresini güncelle
            repo.delete_remote("azure")
        
        # Yeni azure remote'u ekle
        logger.info(f"{repo_name} için 'azure' uzak repository'si oluşturuluyor...")
        azure = repo.create_remote("azure", azure_url)
        
        try:
            azure.fetch()
        except Exception as e:
            logger.warning(f"Azure fetch işlemi başarısız oldu, devam ediliyor: {e}")

        # Repo için senkronizasyon geçmişi yoksa oluştur
        if repo_name not in sync_history:
            sync_history[repo_name] = {}

        # Tüm branch'leri işle
        for remote_ref in origin.refs:
            branch_name = remote_ref.remote_head
            if branch_name == "HEAD":
                continue

            # Değişiklik var mı kontrol et
            changes, current_commit = has_changes(repo, branch_name, sync_history)
            
            if changes:
                try:
                    logger.info(f"🔄 {repo_name}:{branch_name} Azure'a push ediliyor...")
                    azure.push(refspec=f"{branch_name}:{branch_name}", force=True)
                    logger.info(f"🚀 {repo_name}:{branch_name} Azure'a push edildi.")
                    
                    # Senkronizasyon geçmişini güncelle
                    if current_commit:
                        sync_history[repo_name][branch_name] = current_commit
                        write_sync_history(sync_history)
                    
                except Exception as e:
                    logger.error(f"❌ {repo_name}:{branch_name} Azure'a push edilemedi: {e}")
                    continue
            else:
                logger.info(f"✓ {repo_name}:{branch_name} zaten güncel.")

        logger.info(f"✅ {repo_name} senkronizasyonu tamamlandı.")

    except Exception as e:
        logger.error(f"❌ Hata: {repo_name} senkronize edilemedi - {str(e)}")

# Ana işlem
if __name__ == "__main__":
    if not os.path.exists(WORKING_DIR):
        os.makedirs(WORKING_DIR)

    # Senkronizasyon geçmişini oku
    sync_history = read_sync_history()
    
    start_time = time.time()
    repos = get_bitbucket_repos()
    logger.info(f"Toplam {len(repos)} repo bulundu.")

    # Çoklu işlem için işçi havuzu oluştur
    pool = Pool(processes=os.cpu_count() // 2 or 1)
    pool.map(sync_repo, repos)
    pool.close()
    pool.join()

    end_time = time.time()
    logger.info(f"✅ Senkronizasyon tamamlandı. (Toplam süre: {end_time - start_time:.2f} saniye)")
