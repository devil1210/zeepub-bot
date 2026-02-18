import os
import shutil


def cleanup():
    skills_dir = r"c:\Users\charl\Downloads\Zeepub-bot\.agent\skills"
    keep = {
        "production-code-audit",
        "systematic-debugging",
        "python-patterns",
        "senior-architect",
        "postgres-best-practices",
        "backend-dev-guidelines",
        "api-documentation-generator",
        "docker-expert",
        "telegram-bot-builder",
        "ai-agents-architect",
        "subagent-driven-development",
        "skill-developer",
        "rag-implementation",
        "ui-ux-pro-max",
        "react-patterns",
        "telegram-mini-app",
        "mobile-design",
        "typescript-expert",
        "async-python-patterns",
        "git-pushing",
        "lint-and-validate",
        "gemini-api-dev",
        "bash-linux",
    }

    if not os.path.exists(skills_dir):
        print(f"Directory {skills_dir} not found.")
        return

    for item in os.listdir(skills_dir):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path):
            if item not in keep:
                print(f"Removing skill: {item}")
                shutil.rmtree(item_path)
            else:
                print(f"Keeping skill: {item}")
        else:
            # Keep metadata files in the root of skills_dir
            print(f"Keeping file: {item}")


if __name__ == "__main__":
    cleanup()
