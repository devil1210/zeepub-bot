from repositories.user_repository import user_repo
from repositories.publication_repository import pub_repo

print(f"user_repo has list_users: {hasattr(user_repo, 'list_users')}")
print(f"pub_repo has get_full_queue: {hasattr(pub_repo, 'get_full_queue')}")

# Try to see if there are any name collisions
import repositories.user_repository
import repositories.publication_repository
print(f"UserRepository class has list_users: {hasattr(repositories.user_repository.UserRepository, 'list_users')}")
print(f"_PubRepoCompat class has get_full_queue: {hasattr(repositories.publication_repository._PubRepoCompat, 'get_full_queue')}")
