from django.shortcuts import render, redirect
from smart_api_integration.forms import UserLoginForm
from smart_api_integration.models import UserApiCredentials
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User, auth 
from django.db import IntegrityError



def register(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password= request.POST['confirm_password']

        if password == confirm_password:
            
            if User.objects.filter(username=username).exists():
                messages.error(request,"User already exists....")
                return render(request,'accounts/register.html')
            else:
                user = User.objects.create_user(username=username, password=password)
                user.save()
                messages.success(request,"User registered successfully..!")
                return redirect('/')

        else:
            messages.error(request,"Password not matching...")
            return render(request, 'accounts/register.html')

        # try:
        #     user = User.objects.create_user(username=username, password=password)
        #     messages.success(request, "User registered successfully!")
        #     print("User created successfully")
        #     return redirect('/')
        # except IntegrityError:
        #     messages.error(request, "Username already exists. Please choose another one.")
        #     render(request, 'accounts/register.html')
    else:
        return render(request,'accounts/register.html')


def login(request):
    """
    Handle user login with username and passcode.
    If the user doesn't exist, redirect to api_details page to save credentials.
    """
    if request.method == "POST":
        # form = UserLoginForm(request.POST)
        # if form.is_valid():
        #     username = form.cleaned_data['username']
        #     passcode = form.cleaned_data['passcode']
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']


            user = auth.authenticate(username=username, password=passcode)

            if user is not None:
                auth.login(request, user)
                return(request, 'profile')
            else:
                messages.error(request, 'invalid credentials')
                return redirect('/')
        
    else:
        return render(request,'accounts/login.html')
            
            # # Check if user exists
            # try:
            #     user = User.objects.get(username=username)

            #     try:
            #         user_credentials = UserApiCredentials.objects.get(user=user)
                    
            #         # Authenticate user with passcode (assuming simple passcode matching)
            #         if user_credentials.passcode == passcode:
                        
            #             login(request, user)
            #             # Proceed to token check and dashboard
            #             return redirect('smart_api_integration:check_token_and_dashboard')
                        
            #         else:
            #             messages.error(request, "Incorrect passcode.")
            #     except UserApiCredentials.DoesNotExist:
            #         messages.error(request, "User not found. Please provide API credentials.")
            #         return redirect('smart_api_integration:api_details')
            # except User.DoesNotExist:
            #     # Redirect admin to add the user
            #     messages.info(request, "User not found.")            


    # else:
    #     form = UserLoginForm()

    # return render(request, 'accounts/login.html')