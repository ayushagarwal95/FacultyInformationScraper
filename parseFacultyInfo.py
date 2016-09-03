from BeautifulSoup import BeautifulSoup
import mechanize
from StringIO import StringIO
from PIL import Image
from CaptchaParser import CaptchaParser
import cookielib
import json
import sys, getopt
from clint.textui import colored, puts
from clint import arguments
import os
import ssl

facultyInfo = []

REGNO = ''
PASSWORD = ''

def login():
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    cj = cookielib.CookieJar()
    br.set_cookiejar(cj)
    response = br.open('https://vtop.vit.ac.in/student/stud_login.asp')
    print 'Opened Login Form'
    html = response.read()
    soup = BeautifulSoup(html)
    im = soup.find('img', id='imgCaptcha')
    image_response = br.open_novisit(im['src'])
    img = Image.open(StringIO(image_response.read()))
    parser = CaptchaParser()
    captcha = parser.getCaptcha(img)
    br.select_form('stud_login')
    br.form['regno'] = REGNO
    br.form['passwd'] = PASSWORD
    br.form['vrfcd'] = str(captcha)
    print br.form
    print str(captcha) + ' Captcha Parsed'
    br.submit()
    print br
    print 'Submitted'
    if (br.geturl() == 'https://vtop.vit.ac.in/student/home.asp'):
        puts(colored.yellow("LOGIN SUCCESSFUL"))
        return br
    else:
        print 'Could not login'
        return None


def parseFacultyPage(br, facultyID):
    if (br is None):
        return None

    br.open('https://vtop.vit.ac.in/student/stud_home.asp')
    response = br.open('https://vtop.vit.ac.in/student/official_detail_view.asp?empid=' + str(facultyID))
    html = response.read()
    soup = BeautifulSoup(html)
    tables = soup.findAll('table')

    # Extracting basic information of the faculty
    infoTable = tables[0].findAll('tr')
    name = infoTable[2].findAll('td')[1].text
    if (len(name) is 0):
        return None
    school = infoTable[3].findAll('td')[1].text
    designation = infoTable[4].findAll('td')[1].text
    room = infoTable[5].findAll('td')[1].text
    intercom = infoTable[6].findAll('td')[1].text
    email = infoTable[7].findAll('td')[1].text
    division = infoTable[8].findAll('td')[1].text
    additional_role = infoTable[9].findAll('td')[1].text

    # Parsing the open hours of the faculties
    openHours = []
    try:
        dayOne = infoTable[10].findAll('table')[0].findAll('tr')[1].findAll('td')[0].text
        dayTwo = infoTable[10].findAll('table')[0].findAll('tr')[2].findAll('td')[0].text
        startDayOne = infoTable[10].findAll('table')[0].findAll('tr')[1].findAll('td')[1].text
        startDayTwo = infoTable[10].findAll('table')[0].findAll('tr')[2].findAll('td')[1].text
        endDayOne = infoTable[10].findAll('table')[0].findAll('tr')[1].findAll('td')[2].text
        endDayTwo = infoTable[10].findAll('table')[0].findAll('tr')[2].findAll('td')[2].text
        openHours.append({'day': dayOne, 'start_time': startDayOne, 'end_time': endDayOne})
        openHours.append({'day': dayTwo, 'start_time': startDayTwo, 'end_time': endDayTwo})
    except IndexError:
        openHours = []

    outputPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    if os.path.isdir(outputPath) is False:
        os.makedirs(outputPath)
    result = {'empid': facultyID, 'name': name, 'school': school, 'designation': designation, 'room': room, 'intercom': intercom, 'email': email, 'division': division, 'open_hours': openHours}
    with open('output/' + str(facultyID) + '.json', 'w') as outfile:
        json.dump(result, outfile,indent=4)
    return result


def aggregate():
    br = login()
    for i in range(10000, 20000, 1):
        result = parseFacultyPage(br, i)
        if (result is not None):
            puts(colored.green("Parsed FacultyID = " + str(i)))
            facultyInfo.append(result)
            data = {'faculty_info': facultyInfo}
            with open('faculty_info.json', 'w') as outfile:
             json.dump(data, outfile,indent=4)
        else:
            puts(colored.red("Skipped FacultyID = " + str(i)))


if __name__ == '__main__':
    print "-" * 40
    puts(colored.white(" " * 15 + "Faculty Information Scraper"))
    print "-" * 40
    args = arguments.Args()
    REGNO = str(args.get(0))
    PASSWORD = str(args.get(1))
    aggregate()
