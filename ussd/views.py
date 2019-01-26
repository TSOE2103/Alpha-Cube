from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .utilities.SMS import SMS
from .utilities.location import sortlocations
from .models import Victim, Volunteer
from evacroutes.models import Update
import requests

@csrf_exempt
def ussdrelief(request):
    if request.method == 'POST':
        session_id = request.POST.get('sessionId')
        service_code = request.POST.get('serviceCode')
        phone_number = request.POST.get('phoneNumber')
        text = request.POST.get('text')

        response = ""
        
        volunteer = Volunteer.objects.filter(phone_number=phone_number)
        volunteer = list(volunteer)[0]
        if(volunteer):
            victims=Victim.objects.filter(volunteer=volunteer)
            victims = list(victims)
            if text == "":
                response = "CON What do you want to do\n"
                response += "1. List people in need\n"
                response += "2. Send an alert\n"

            elif text[0] == '1':
                textlist=text.split('*')
                idx=textlist.count('1')-textlist.count('0')
                if(text[-1]==5):
                    victims[idx].setRescued(True)
                    victims[idx].save()
                    idx+=1
                if idx==len(victims):
                    response+="END The list has ended\n"
                elif idx==len(victims)-1:
                    response+="END "
                else:
                    response+="CON "
                if idx!=len(victims):
                    response+=victims[idx].location
                    response+="\nPress 5 to indicate victim has rescued\n"
                    if idx!=len(victims)-1:
                        response+="Press 1 to for next\n"
                    if idx!=0:
                        response+="Press 0 to for back\n"
                

            elif text == "2":
                response = "END Send the alert via SMS to\n"
                response+="86387 as\n"
                response+="ALERT text"

        else:
            response = "END Please send the nearest\n"
            response += "landmark to 86387 via SMS\n"
            response += "along with your pincode"

        return HttpResponse(response)
    else:
        return HttpResponse("Response can't be made")

@csrf_exempt
def sms(request):
    if request.method == 'POST':
        fro = request.POST.get('from')
        to = request.POST.get('to')
        text = request.POST.get('text')
        date = request.POST.get('date')
        id = request.POST.get('id')
        print(to)
        query=text.replace(' ', '%20')
        key='Aqxws6GyR0KaQH-uo9w92nqNeePHAzsbkVDbrpiayIiAwfTbXcML-wj1XLEBPQcQ'
        url='http://dev.virtualearth.net/REST/v1/Locations?q='+query+'&o=json&key='+key
        result=requests.get(url)
        result=result.json()
        lat,lon=result['resourceSets'][0]['resources'][0]['point']['coordinates']
        if to=="86386":
            victim=Victim.objects.filter(phone_number=fro)
            if(victim):
                victim=list(victim)[0]
                victim.updateLocation(lat,lon,text)
            else:
                victim=Victim(phone_number=fro,lat=lat,lon=lon,location=text,rescued=True)
            volunteer=sortlocations(victim.lat,victim.lon,list(Volunteer.objects.all()))[0]
            victim.assign(volunteer=volunteer)
            victim.save()
            recipients=["+"+str(victim.phone_number)]
            message="You have been assigned volunteer at "+volunteer.location+". For help, send HELP message to 86387"
            SMS().send_sms_sync(recipients=recipients,message=message)
        elif to=="86387" and text[:5]=="ALERT":
            volunteer=list(Volunteer.objects.filter(phone_number=fro))[0]
            victims=Victim.objects.filter(volunteer=volunteer)
            recipients=["+"+str(victim.phone_number) for victim in list(victims)]
            message=text[6:]
            SMS().send_sms_sync(recipients=recipients,message=message)
        elif to=="86387" and text[:4]=="HELP":
            victim=list(Victim.objects.filter(phone_number=fro))[0]
            recipients=["+"+str(victim.volunteer.phone_number)]
            message=text[5:]
            SMS().send_sms_sync(recipients=recipients,message=message)
        elif to=="86387":
            volunteer=Volunteer(phone_number=fro,lat=lat,lon=lon,location=text)
            volunteer.save()
        return HttpResponse("Success")

@csrf_exempt
def index(request):
    if request.method == 'POST':
        session_id = request.POST.get('sessionId')
        service_code = request.POST.get('serviceCode')
        phone_number = request.POST.get('phoneNumber')
        text = request.POST.get('text')

        response = ""
        
        victim = Victim.objects.filter(phone_number=phone_number)
        if(victim):
            victim=list(victim)[0]
            updates = Update.objects.order_by('time')
            updateslist = list(updates)
            if text == "":
                response = "CON What do you want to do\n"
                response += "1. Ask for support\n"
                response += "2. Latest news\n"
                response += "3. Reach a Shelter\n"

            elif text == "1":
                victim.setRescued(False)
                victim.save()
                response += "CON Dont worry. Stay Strong\n"
                response+="Our response team will soon be there for you\n"
                response+="1.Update your Location\n"
                response += "2.Cancel request for help"

            elif text == "1*1":
                response = "END Please send the new\n"
                response += "landmark to 86386 via SMS\n"
                response += "along with your pincode"
            
            elif text == "1*2":
                victim.save()
                victim.setRescued(True)
                response += "END We are glad that you safe now\n"

            elif text[0] == '2':
                textlist=text.split('*')
                idx=textlist.count('1')-textlist.count('0')
                if idx==len(updates)-1:
                    response+="END "
                else:
                    response+="CON "
                response+=updateslist[idx].message
                response+="\n"
                if idx!=len(updates)-1:
                    response+="Press 1 for next\n"
                if idx!=0:
                    response+="Press 0 for back\n"
            elif text == "3":
                response += "CON "
                volunteers=sortlocations(victim.lat,victim.lon,list(Volunteers.objects.all()))
                textlist=text.split('*')
                idx=textlist.count('9')-textlist.count('7')
                if(text[-1]==5):
                    victim.assign(volunteers[idx])
                    response+="END You have been assigned\n"
                    response+="volunteer at "+volunteers[idx].location+". You can ask\n"
                    response+="for help by sending HELP message\n"
                    response+="to 86387\n"
                else:
                    response+="CON "
                if idx!=len(volunteers):
                    response+=volunteers[idx].location
                    response+="\nPress 5 to ask help or reach the shelter\n"
                    if idx!=len(volunteers)-1:
                        response+="Press 9 for next\n"
                    if idx!=0:
                        response+="Press 7 for back\n"

        else:
            response = "END Please send the nearest\n"
            response += "landmark to 86386 via SMS\n"
            response += "along with your pincode"

        return HttpResponse(response)
    else:
        return HttpResponse("Response can't be made")
