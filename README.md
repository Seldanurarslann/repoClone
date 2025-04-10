# Bitbucket reposunun Azure DevOps'a taşıma Scripti

Bu Python scripti, Bitbucket repository'lerini Azure DevOps ile senkronize etmenizi sağlar. Bitbucket'taki repository'ler, Azure DevOps'taki karşılıklarıyla güncellenir. Hem yerel hem de uzak değişiklikler senkronize edilir.

## Özellikler
- Bitbucket'taki repository'leri Azure DevOps'a senkronize eder.
- Değişiklikleri kontrol eder ve yalnızca yeni değişiklikler varsa senkronizasyon yapar.
- Tüm branch'ler için senkronizasyon işlemi yapar.
- Senkronizasyon geçmişini kaydeder ve geçmiş commit'lere göre değişiklik kontrolü yapar.
- Çift işlemli bir yapıya sahiptir ve işlem hızını artırmak için çoklu işlem kullanır.

## Gereksinimler
- Python 3.x
- `requests`, `gitpython`, `python-dotenv`, `multiprocessing` gibi Python paketleri.

## Kurulum

1. **Python ve gerekli paketleri yükleyin:**

   Öncelikle Python 3 ve gerekli paketleri yüklemeniz gerekir. `requirements.txt` dosyasını oluşturup aşağıdaki paketleri yükleyebilirsiniz:

   ```bash
   pip install -r requirements.txt
   
   `requirements.txt` dosyasını oluşturmak için:
   
   ```bash
   requests
   gitpython
   python-dotenv
   
2.  **`.env` Dosyasını Yapılandırma**
   
   Çalıştırılmadan önce `.env` dosyasının doğru şekilde yapılandırılması gerekmektedir. Bu dosyada aşağıdaki ortam değişkenlerini belirleyin:

  ```bash
    WORKING_DIR=./repos  # Yerel repo dizini
    BITBUCKET_WORKSPACE_ID=<BITBUCKET_WORKSPACE_ID>  # Bitbucket workspace ID
    BITBUCKET_USERNAME=<BITBUCKET_USERNAME>  # Bitbucket kullanıcı adı
    BITBUCKET_PAT=<BITBUCKET_PERSONAL_ACCESS_TOKEN>  # Bitbucket kişisel erişim token
    AZURE_ORG=<AZURE_ORG>  # Azure organizasyon adı
    AZURE_PROJECT=<AZURE_PROJECT>  # Azure proje kimliği
    AZURE_PROJECT_NAME=<AZURE_PROJECT_NAME>  # Azure proje adı
    AZURE_PAT=<AZURE_PERSONAL_ACCESS_TOKEN>  # Azure kişisel erişim token
    SYNC_HISTORY_FILE=sync_history.json  # Senkronizasyon geçmişini saklamak için dosya adı
    
3.  **Scripti Çalıştırma:**

   Bu scripti çalıştırmak için terminalde şu komutu kullanabilirsiniz:

 ```bash
    python main.py
 ```

   Script, Bitbucket'taki repository'leri Azure DevOps'a senkronize etmeye başlayacaktır. Tüm işlem süresi konsola yazdırılır.


   


