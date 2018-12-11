import sys
import urllib3
import bs4
import re

def get_tibo_services(httpclient: urllib3.PoolManager, httptibcodaemon: str):
    url = httptibcodaemon +'/services'
    response = httpclient.request('GET', url)
    print(f'Querying {url}')
    
    parsed = bs4.BeautifulSoup(response.data, 'html.parser')
    table = parsed.find_all('table')    
    return [item.text for item in table[4].find_all('a')]

def prefix_halfitem_with(prefix1:str, prefix2:str, collection: list):
    retvalue = []
    for i in range(0, len(collection)):
        if i < len(collection) / 2:
            retvalue.append(prefix1 + collection[i])
        else:
            retvalue.append(prefix2 + collection[i])
    return retvalue

def get_service_info_headline_details(soup : bs4.BeautifulSoup, service : int):
    table = soup.find_all('table')    

    # grab Service headline information @ /service_detail?7800
    headline_title = [item.text for item in table[4].find_all('td')][0].split(':')    
    headline_info = [h.nextSibling for h in table[4].find_all('td')[1].find_all('br')] # some hack voodoo to get
    headline_info.insert(0, str(service))

    headlineinfo_zip = zip(headline_title, headline_info)
    return dict(headlineinfo_zip)

def get_service_info_iorates(soup : bs4.BeautifulSoup):
    inout_block = soup.find(text='Inbound Rates (per second)').parent
    inout_data_block = inout_block.findParent('table').find_all('tr')        
    io_rates_titles = [item.text for item in inout_data_block[1].find_all('b')]
    io_rates_titles = prefix_halfitem_with('in_', 'out_', io_rates_titles)
    
    io_rates_values = [item.text for item in inout_data_block[2].find_all('font')]
    io_rates_zip = zip(io_rates_titles, io_rates_values)
    return dict(io_rates_zip)

def get_service_info_iocount(soup : bs4.BeautifulSoup):
    inout_block = soup.find(text='Inbound Counts').parent
    inout_data_block = inout_block.findParent('table').find_all('tr')        
    io_count_titles = [item.text for item in inout_data_block[1].find_all('b')]

    io_count_titles = prefix_halfitem_with('in_', 'out_', io_count_titles)

    io_count_values = [item.text for item in inout_data_block[2].find_all('font')]
    io_count_zip = zip(io_count_titles, io_count_values)
    return dict(io_count_zip)

def get_service_info_inoutbound_packet_stats(paketStatsTitle: str, soup : bs4.BeautifulSoup):
    inout_block = soup.find(text=paketStatsTitle).parent
    inout_data_block = inout_block.findParent('table').find_all('tr')        
    io_count_titles = [item.text for item in inout_data_block[1].find_all('b')]    
    io_count_values = [item.text for item in inout_data_block[2].find_all('font')]
    io_count_zip = zip(io_count_titles, io_count_values)
    return dict(io_count_zip)

def get_service_info_inbound_packet_stats(soup : bs4.BeautifulSoup):        
    return get_service_info_inoutbound_packet_stats('Inbound Packet Totals', soup)

def get_service_info_outbound_packet_stats(soup : bs4.BeautifulSoup):    
    return get_service_info_inoutbound_packet_stats('Outbound Packet Totals', soup)

def get_tibo_services_info(httpclient: urllib3.PoolManager, httptibcodaemon: str, service : int):
    url = httptibcodaemon +'/service_detail?'+service
    response = httpclient.request('GET', url)
    print(f'Querying {url}')
    
    parsed = bs4.BeautifulSoup(response.data, 'html.parser')
    
    service_info = {'headline_info': get_service_info_headline_details(parsed, service)}
    service_info['io_rates'] = get_service_info_iorates(parsed)
    service_info['io_count'] = get_service_info_iocount(parsed)
    service_info['inbound_paket_stats'] = get_service_info_inbound_packet_stats(parsed)
    service_info['outbound_paket_stats'] = get_service_info_outbound_packet_stats(parsed)

    return service_info

def get_tibo_ipaddress(httpclient: urllib3.PoolManager, httptibcodaemon: str):
    url = httptibcodaemon +'/current_log'
    response = httpclient.request('GET', url)
    print(f'Querying {url}')
    
    parsed = bs4.BeautifulSoup(response.data, 'html.parser')
    currentlog = parsed.find('textarea').text.replace('\xa0',' ')
    
    return re.findall(r'Detected IP interface: (.*?)\s\(IP', currentlog, re.MULTILINE)


def get_tibco_details(hostname):        
    httpclient = urllib3.PoolManager()
    tibdaemonhttp = 'http://' + hostname + ':7580'    

    ipinterfaces = get_tibo_ipaddress(httpclient, tibdaemonhttp)
    services = get_tibo_services(httpclient, tibdaemonhttp)

    print("IP interfaces", ipinterfaces)
    for service in services:
        service_info = get_tibo_services_info(httpclient, tibdaemonhttp, service)
        print(service_info)
    pass
    

def main(argv):
    # My code here
    if len(argv) < 2:
        print("Usage: webscrape machinename")
    else:
        get_tibco_details(argv[1])
    print(argv)
    
    pass

if __name__ == "__main__":
    main(sys.argv)
