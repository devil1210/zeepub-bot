import json
import os
import sys

# La ruta base para la infraestructura del equipo
TEAM_DIR = ".antigravity/team"

def init_team():
    """Inicializa la infraestructura del equipo EvilTeams."""
    os.makedirs(f"{TEAM_DIR}/mailbox", exist_ok=True)
    os.makedirs(f"{TEAM_DIR}/locks", exist_ok=True)
    tasks_path = f"{TEAM_DIR}/tasks.json"
    if not os.path.exists(tasks_path):
        with open(tasks_path, 'w', encoding='utf-8') as f:
            json.dump({"tasks": [], "members": []}, f, indent=2, ensure_ascii=False)
    if not os.path.exists(f"{TEAM_DIR}/broadcast.msg"):
        with open(f"{TEAM_DIR}/broadcast.msg", 'w', encoding='utf-8') as f: 
            f.write("")
    print(f"✓ Infraestructura 'EvilTeams' (Dirigida por Kaguya) lista en {TEAM_DIR}.")

def assign_task(title, assigned_to, deps=[]):
    """Asigna una nueva tarea con soporte para dependencias."""
    path = f"{TEAM_DIR}/tasks.json"
    if not os.path.exists(path):
        init_team()
        
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    task = {
        "id": len(data["tasks"]) + 1,
        "title": title,
        "status": "PENDING",
        "plan_approved": False,
        "assigned_to": assigned_to,
        "dependencies": deps
    }
    data["tasks"].append(task)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Tarea {task['id']} ({title}) asignada a {assigned_to}.")

def broadcast(sender, text):
    """Envía un mensaje a todos los miembros del equipo."""
    msg = {"de": sender, "tipo": "BROADCAST", "mensaje": text}
    with open(f"{TEAM_DIR}/broadcast.msg", 'a', encoding='utf-8') as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    print(f"✓ Mensaje global enviado por {sender}.")

def send_message(sender, receiver, text):
    """Envía un mensaje al buzón de un agente específico."""
    msg = {"de": sender, "mensaje": text}
    with open(f"{TEAM_DIR}/mailbox/{receiver}.msg", 'a', encoding='utf-8') as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    print(f"✓ Mensaje enviado a {receiver}.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init": 
            init_team()
        elif cmd == "assign":
            if len(sys.argv) >= 4:
                assign_task(sys.argv[2], sys.argv[3])
            else:
                print("Uso: python team_manager.py assign <title> <assigned_to>")
    else:
        print("Comandos: init, assign, broadcast, send")
