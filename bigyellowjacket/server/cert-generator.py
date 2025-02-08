from OpenSSL import crypto
from pathlib import Path

def generate_self_signed_cert():
    """Generate self-signed certificate and private key"""
    # Create certificates directory if it doesn't exist
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    # Generate key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)
    
    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().CN = "localhost"
    cert.get_subject().O = "Big Yellow Jacket"
    cert.get_subject().OU = "Security System"
    cert.get_subject().C = "US"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # Save certificate
    with open("certs/server.crt", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    # Save private key
    with open("certs/server.key", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    
    print("Certificate and private key generated successfully!")
    print(f"Certificate saved to: {Path('certs/server.crt').absolute()}")
    print(f"Private key saved to: {Path('certs/server.key').absolute()}")

if __name__ == "__main__":
    generate_self_signed_cert()
