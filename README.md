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
2. **requirements.txt dosyasını oluşturmak için:**
   ```bash
   requests
   gitpython
   python-dotenv

