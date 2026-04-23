import time
from umbral_pre import SecretKey, Signer, encrypt, generate_kfrags, reencrypt

def benchmark_pre():
    print("Initializing PRE Benchmarking...")
    
    # 1. จำลองฝั่ง Data Owner (Alice) สร้างกุญแจและเข้ารหัสข้อมูล
    alices_secret_key = SecretKey.random()
    alices_public_key = alices_secret_key.public_key()
    alices_signer = Signer(alices_secret_key)
    
    # 2. จำลองฝั่ง Requester (Bob)
    bobs_secret_key = SecretKey.random()
    bobs_public_key = bobs_secret_key.public_key()
    
    # 3. เข้ารหัสข้อมูลจำลอง
    plaintext = b'6G IoT Sensor Data'
    capsule, ciphertext = encrypt(alices_public_key, plaintext)
    
    # 4. สร้าง Re-encryption Key (KFrag) เพื่อมอบสิทธิ์ให้ Bob
    # ในสถาปัตยกรรมของคุณ ขั้นตอนนี้คือการสร้าง RK_{DO -> AR}
    kfrags = generate_kfrags(delegating_sk=alices_secret_key,
                             receiving_pk=bobs_public_key,
                             signer=alices_signer,
                             threshold=1,
                             shares=1,
			     sign_delegating_key=True,
                             sign_receiving_key=True)
    kfrag = kfrags[0]
    
    # --- เริ่มต้นการจับเวลา (เฉพาะขั้นตอน Cross-Domain ที่ Proxy Gateway) ---
    iterations = 1000
    print(f"Running PRE transformation {iterations} times to get average...")
    
    start_time = time.time()
    
    for _ in range(iterations):
        # นี่คือ Operation T_PRE ที่เราต้องการวัด
        cfrag = reencrypt(capsule=capsule, kfrag=kfrag)
        
    end_time = time.time()
    # -----------------------------------------------------------
    
    # คำนวณเวลาเฉลี่ยเป็นมิลลิวินาที (ms)
    total_time = end_time - start_time
    avg_time_ms = (total_time / iterations) * 1000
    
    print("\n" + "="*40)
    print(f"Result: Average T_PRE time = {avg_time_ms:.4f} ms")
    print("="*40)

if __name__ == "__main__":
    benchmark_pre()
