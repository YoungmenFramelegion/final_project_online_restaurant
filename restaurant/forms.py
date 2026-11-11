"""Django-ის მომხმარებლის რეგისტრაციისა და შესვლის ფორმები."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


# რეგისტრაციის ფორმა: მომხმარებლის სახელი, პაროლი და პაროლის გამეორება.
# Django თვითონ ამოწმებს პაროლის პირობებს და ქმნის ანგარიშს.
class RegisterForm(UserCreationForm):
    # ვუთითებთ, რომ ანგარიშისთვის Django-ის ჩაშენებული User მოდელი გამოიყენება.
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    # ფორმის ველებს ქართულ დასახელებებს ვაძლევთ.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "მომხმარებლის სახელი"
        self.fields["password1"].label = "პაროლი"
        self.fields["password2"].label = "გაიმეორე პაროლი"
        for field in self.fields.values():
            field.help_text = ""


# შესვლის ფორმა: მომხმარებლის სახელი და პაროლი.
# პაროლის შემოწმებას Django აკეთებს, არა ჩვენი JavaScript.
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="მომხმარებლის სახელი")
    password = forms.CharField(label="პაროლი", widget=forms.PasswordInput)
