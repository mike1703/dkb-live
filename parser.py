from io import StringIO

import requests
from lxml import etree

import smtplib
from secrets import secrets, sender, recipients
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

html = requests.get("https://www.dkb.de/dkb-live/")
html_string = StringIO(html.text)
result = etree.parse(html_string, etree.HTMLParser())

# get offers
texts = result.xpath("//body/div/div/div/div/div/div/div[@class='clearfix textDefaultModule dkbaktionen grid_1']/div/p/a/text()")
texts = [text.strip() for text in texts]
links = result.xpath("//body/div/div/div/div/div/div/div[@class='clearfix textDefaultModule dkbaktionen grid_1']/div/p/a/@href")
links = ["https://www.dkb.de{}".format(link.strip()) for link in links]
images = result.xpath("//body/div/div/div/div/div/div/div[@class='clearfix textDefaultModule dkbaktionen grid_1']/div/div/a/picture/source/@srcset")
images = ["https://www.dkb.de{}".format(image.strip()) for image in images]

results = sorted(list(zip(texts, links, images)))
offer_lines = []
for result in results:
    offer_lines.append('<a href="{}"><img src="{}"/>{}</a><br/>'.format(result[1],result[2], result[0]))

text_string = "\n".join(["{} - {}".format(result[0], result[1]) for result in results])
html_string = "<html><body><div>{}</div></body></html>".format("".join(offer_lines))

with open("offer.html", "r+") as outfile:
    old_html_string = outfile.readline()
    if html_string != old_html_string:
        # there was a change since last parsing
        outfile.seek(0)
        outfile.write(html_string)

        # create html email with text alternative
        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "DKB Live Angebote haben sich geändert"
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)
        msg["Date"] = formatdate(localtime=True)

        # Create the body of the message (a plain-text and an HTML version).
        text = text_string
        html = html_string

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        # Send the message via local SMTP server.
        s = smtplib.SMTP(secrets['server'], secrets['port'])
        s.starttls()
        s.login(secrets['user'], secrets['password'])
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail(sender, recipients, msg.as_string())
        s.quit()