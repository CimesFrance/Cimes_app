import os
import json
import smtplib
from email.message import EmailMessage
from tkinter import messagebox

def envoyer_email_rapport(destinataire, chemin_pdf, subject="Rapport de Granulométrie CIMES", body="Veuillez trouver ci-joint le rapport de granulométrie généré par l'application CIMES."):
    """
    Envoie un email avec le fichier PDF en pièce jointe via Gmail.
    Nécessite un fichier 'secrets.json' dans CIMES_Settings avec 'gmail_app_password'.
    """
    # 1. Vérification des identifiants
    settings_dir = os.path.join(os.path.expanduser("~"), "CIMES_Settings")
    secrets_file = os.path.join(settings_dir, "secrets.json")
    
    sender_email = "Yannngassa35@gmail.com"
    app_password = None
    
    if os.path.exists(secrets_file):
        try:
            with open(secrets_file, 'r', encoding='utf-8') as f:
                secrets = json.load(f)
                app_password = secrets.get("gmail_app_password")
        except Exception as e:
            print(f"[EMAIL] Erreur lecture secrets.json : {e}")
            
    if not app_password:
        messagebox.showerror(
            "Erreur d'envoi",
            f"Impossible d'envoyer l'e-mail. Vous devez d'abord configurer le mot de passe d'application pour {sender_email}.\n\n"
            f"Veuillez créer un fichier 'secrets.json' dans {settings_dir} contenant:\n"
            '{"gmail_app_password": "votre_mot_de_passe_16_lettres"}'
        )
        return False
        
    # 2. Création de l'email
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = destinataire
    msg.set_content(body)
    
    # 3. Attachement du PDF
    if os.path.exists(chemin_pdf):
        try:
            with open(chemin_pdf, 'rb') as f:
                pdf_data = f.read()
            msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=os.path.basename(chemin_pdf))
        except Exception as e:
            print(f"[EMAIL] Erreur attachement PDF : {e}")
            return False
    else:
        print(f"[EMAIL] Fichier PDF introuvable : {chemin_pdf}")
        return False
        
    # 4. Envoi via SMTP Gmail
    try:
        print(f"[EMAIL] Connexion à smtp.gmail.com pour envoi à {destinataire}...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        print(f"[EMAIL] E-mail envoyé avec succès à {destinataire}")
        return True
    except smtplib.SMTPAuthenticationError:
        messagebox.showerror("Erreur d'authentification", 
            "Mot de passe d'application Gmail invalide. Vérifiez votre fichier secrets.json.")
        return False
    except Exception as e:
        messagebox.showerror("Erreur d'envoi", f"Une erreur est survenue lors de l'envoi de l'e-mail :\n{e}")
        return False
