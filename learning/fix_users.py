from learning.models import User

print("Fixing all users...")

users = User.objects.all()
print(f"Found {users.count()} users\n")

for user in users:
    print(f"User: {user.username}")
    
    # Activate user
    if not user.is_active:
        user.is_active = True
        print("  ✅ Activated user")
    else:
        print("  ✓ Already active")
    
    # Check password hash
    if user.password.startswith('pbkdf2_sha256$'):
        print("  ✓ Password properly hashed")
    else:
        print(f"  ⚠ Password NOT hashed! Current: {user.password[:20]}...")
        # Don't auto-reset - user needs to do it manually
        print("  → Run: user.set_password('new_password') in shell")
    
    user.save()
    print()

print("Done!")