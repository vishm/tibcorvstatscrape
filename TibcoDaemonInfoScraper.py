import urllib3
import bs4
import re


class TibcoDaemonServiceInfo:
    def __init__(self:any, hostname: str, listeningInterfaces: str, services_info):
        self._hostname = hostname
        self._ipinterfaces = listeningInterfaces
        self._services_info = services_info
        pass
    
    @property
    def hostname(self:any):
        return self._hostname
    
    @property
    def ipinterfaces(self:any):
        return self._ipinterfaces

    @property
    def services_info(self:any):
        return self._services_info


class TibcoDaemonInfoScraper:
    def __init__(self: any, daemonhostname: str):
        self.daemonhostname = daemonhostname
        self.tibdaemonhttp = 'http://' + daemonhostname + ':7580'
        self.httpclient = urllib3.PoolManager()

    def get_tibco_details(self: any):
        ipinterfaces = self._get_tibo_ipaddress(
            self.httpclient, self.tibdaemonhttp, timeoutInSec=3.0)
        services = self._get_tibo_services(
            self.httpclient, self.tibdaemonhttp, timeoutInSec=3.0)

        services_info = []
        for service in services:
            service_info = self._get_tibo_services_info(
                self.httpclient, self.tibdaemonhttp, service, timeoutInSec=3.0)
            services_info.append(service_info)
            
        retInfo = TibcoDaemonServiceInfo(self.daemonhostname, ipinterfaces, services_info)
        return retInfo

    def _get_tibo_services(self: any, httpclient: urllib3.PoolManager, httptibcodaemon: str, timeoutInSec: float):
        url = httptibcodaemon + '/services'
        response = self.httpclient.request('GET', url, timeout=timeoutInSec)        

        parsed = bs4.BeautifulSoup(response.data, 'html.parser')
        table = parsed.find_all('table')
        return [item.text for item in table[4].find_all('a')]

    def _prefix_halfitem_with(self: any, prefix1: str, prefix2: str, collection: list):
        retvalue = []
        for i in range(0, len(collection)):
            if i < len(collection) / 2:
                retvalue.append(prefix1 + collection[i])
            else:
                retvalue.append(prefix2 + collection[i])
        return retvalue

    def _get_service_info_headline_details(self: any, soup: bs4.BeautifulSoup, service: int):
        table = soup.find_all('table')

        # grab Service headline information @ /service_detail?7800
        headline_title = [
            item.text for item in table[4].find_all('td')][0].split(':')
        headline_info = [h.nextSibling for h in table[4].find_all(
            'td')[1].find_all('br')]  # some hack voodoo to get
        headline_info.insert(0, str(service))

        headlineinfo_zip = zip(headline_title, headline_info)
        return dict(headlineinfo_zip)

    def _get_service_info_iorates(self: any, soup: bs4.BeautifulSoup):
        inout_block = soup.find(text='Inbound Rates (per second)').parent
        inout_data_block = inout_block.findParent('table').find_all('tr')
        io_rates_titles = [
            item.text for item in inout_data_block[1].find_all('b')]
        io_rates_titles = self._prefix_halfitem_with(
            'in_', 'out_', io_rates_titles)

        io_rates_values = [
            item.text for item in inout_data_block[2].find_all('font')]
        io_rates_zip = zip(io_rates_titles, io_rates_values)
        return dict(io_rates_zip)

    def _get_service_info_iocount(self: any, soup: bs4.BeautifulSoup):
        inout_block = soup.find(text='Inbound Counts').parent
        inout_data_block = inout_block.findParent('table').find_all('tr')
        io_count_titles = [
            item.text for item in inout_data_block[1].find_all('b')]

        io_count_titles = self._prefix_halfitem_with(
            'in_', 'out_', io_count_titles)

        io_count_values = [
            item.text for item in inout_data_block[2].find_all('font')]
        io_count_zip = zip(io_count_titles, io_count_values)
        return dict(io_count_zip)

    def _get_service_info_inoutbound_packet_stats(self: any, paketStatsTitle: str, soup: bs4.BeautifulSoup):
        inout_block = soup.find(text=paketStatsTitle).parent
        inout_data_block = inout_block.findParent('table').find_all('tr')
        io_count_titles = [
            item.text for item in inout_data_block[1].find_all('b')]
        io_count_values = [
            item.text for item in inout_data_block[2].find_all('font')]
        io_count_zip = zip(io_count_titles, io_count_values)

        return dict(io_count_zip)

    def _get_service_info_inbound_packet_stats(self: any, soup: bs4.BeautifulSoup):
        return self._get_service_info_inoutbound_packet_stats('Inbound Packet Totals', soup)

    def _get_service_info_outbound_packet_stats(self: any, soup: bs4.BeautifulSoup):
        return self._get_service_info_inoutbound_packet_stats('Outbound Packet Totals', soup)

    def _get_tibo_services_info(self: any, httpclient: urllib3.PoolManager, httptibcodaemon: str, service: int, timeoutInSec: float):
        url = httptibcodaemon + '/service_detail?'+service
        response = httpclient.request('GET', url, timeout=timeoutInSec)        

        parsed = bs4.BeautifulSoup(response.data, 'html.parser')

        service_info = {
            'headline_info': self._get_service_info_headline_details(parsed, service)}
        service_info['io_rates'] = self._get_service_info_iorates(parsed)
        service_info['io_count'] = self._get_service_info_iocount(parsed)
        service_info['inbound_paket_stats'] = self._get_service_info_inbound_packet_stats(
            parsed)
        service_info['outbound_paket_stats'] = self._get_service_info_outbound_packet_stats(
            parsed)

        return service_info

    def _get_tibo_ipaddress(self: any, httpclient: urllib3.PoolManager, httptibcodaemon: str, timeoutInSec: float):
        url = httptibcodaemon + '/current_log'
        response = httpclient.request('GET', url, timeout=timeoutInSec)        

        parsed = bs4.BeautifulSoup(response.data, 'html.parser')
        currentlog = parsed.find('textarea').text.replace('\xa0', ' ')

        return re.findall(r'face:\s((?:\d{1,3}\.){3}\d{1,3})\s\(IP', currentlog, re.MULTILINE)
