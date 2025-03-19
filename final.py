import requests
import xml.etree.ElementTree as ET
import html

# Send SOAP Request
url = "http://192.168.3.143:8998/service/ContentDirectory_control"
headers = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPACTION": "urn:schemas-upnp-org:service:ContentDirectory:1#Browse"
}

data = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" 
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:Browse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
            <ObjectID>1</ObjectID>
            <BrowseFlag>BrowseDirectChildren</BrowseFlag>
            <Filter>*</Filter>
            <StartingIndex>0</StartingIndex>
            <RequestedCount>10</RequestedCount>
            <SortCriteria></SortCriteria>
        </u:Browse>
    </s:Body>
</s:Envelope>"""

response = requests.post(url, headers=headers, data=data)

# Debug: Print Raw Response
print("Raw Response:\n", response.text)

# Clean and Parse XML
cleaned_xml = response.text.strip()

try:
    root = ET.fromstring(cleaned_xml)  # Parse SOAP response
except ET.ParseError as e:
    print("Error parsing XML:", e)
    exit(1)

# Extract <Result> content
result_data = root.find(".//Result")

if result_data is not None and result_data.text:
    inner_xml = html.unescape(result_data.text)  # Decode & Parse
    try:
        didl_tree = ET.fromstring(inner_xml)
    except ET.ParseError as e:
        print("Error parsing DIDL-Lite XML:", e)
        exit(1)

    # Generate M3U Playlist
    m3u_content = "#EXTM3U\n"

    for item in didl_tree.findall(".//{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item"):
        title_element = item.find("{http://purl.org/dc/elements/1.1/}title")
        url_element = item.find("{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}res")

        if title_element is not None and url_element is not None:
            title = title_element.text.strip()
            url = url_element.text.strip()

            # Format as required
            m3u_content += f'#EXTINF:-1 tvh-epg="disable", {title}\n'
            m3u_content += f'pipe://ffmpeg -loglevel fatal -i "{url}" -vcodec copy -acodec copy -preset medium -f mpegts pipe:1\n'

    # Save M3U file
    with open("tv_channels.m3u", "w") as file:
        file.write(m3u_content)

    print("M3U file created: tv_channels.m3u")

else:
    print("No valid channel data found.")

