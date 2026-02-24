from core.launcher import Launcher

def main():
    launcher = Launcher()
    user_choices = launcher.run()
    
    if user_choices:
        print(f"\n✅ Setup bereit!")
        print(f" └─ Modell: {user_choices['model']}")
        print(f" └─ Datasets: {', '.join(user_choices['datasets'])}")

if __name__ == "__main__":
    main()