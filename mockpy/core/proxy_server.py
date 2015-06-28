#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import httplib
from threading import Thread
import signal
import sys

from libmproxy import controller, proxy
from libmproxy.proxy.server import ProxyServer
from libmproxy.protocol.http import HTTPRequest, HTTPResponse
from netlib.odict import ODictCaseless

import mockpy.utils.extensions
from ..utils.config import *
from mockpy.status.status import Status
from ..utils import log
from ..models.mapping_items_manager import *


class MITMProxy(controller.Master):

    def __init__(self, server, inout_path, res_path, http_proxy):
        controller.Master.__init__(self, server)

        self.http_proxy = http_proxy
        self.handler = MappingItemsManager(inout_path, res_path)
        self.status = Status(self.handler)

        success("Proxy server started")

    def handle_request(self, flow):
        request = flow.request.to_mapper_request()
        mapping_items = self.handler.mapping_item_for_mapping_request(request)

        log.log_url(flow.request.url)

        if Status.is_status(flow.request.url):
            info("Accessing Satus")
            flow.reply(HTTPResponse.with_html(self.status.html_response()))
            log.print_seperator()
            return

        if len(mapping_items) > 1:
            log.log_multiple_matches(mapping_items)

        if len(mapping_items) == 0:
            self.perform_http_request(flow)
        else:
            self.perform_mapping_request(flow, mapping_items[0])

        log.print_seperator()

    def perform_mapping_request(self, flow, mapping_item):
        response, request = mapping_item.response, mapping_item.request

        log.log_request(request)
        log.log_response(response)

        response = HTTPResponse.from_intercepted_response(response)
        flow.reply(response)

    def perform_http_request(self, flow):
        if self.http_proxy is None:
            flow.reply()
        else:
            thread = Thread(target=self.threaded_perform_http_request,
                args=(flow, self.http_proxy))
            thread.start()

    def threaded_perform_http_request(self, flow, proxy_settings):
        response = self.perform_request(flow.request, proxy_settings[0], proxy_settings[1])
        flow.reply(response)

    @staticmethod
    def perform_request(request, url, port):
        try:
            conn = httplib.HTTPConnection(url, port)
            headers = dict(request.headers.items())

            conn.request(request.method, request.url,
                         body=request.content, headers=headers)
            httplib_response = conn.getresponse()

            headers = ODictCaseless.from_httplib_headers(httplib_response.getheaders())
            response = HTTPResponse(code=httplib_response.status,
                                    content=httplib_response.read(),
                                    msg="",
                                    httpversion=(1, 1),
                                    headers=headers)
            return response
        except Exception as ex:
            error("Error Happened")
            error(ex)
            error("method: %s\nurl: %s\nbody: --\nheaders: --" %
                  (request.method, request.url))
            return None


def start_proxy_server(port, inout_path, res_path, http_proxy):
    config = proxy.ProxyConfig(port=port)
    server = ProxyServer(config)
    m = MITMProxy(server, inout_path, res_path, http_proxy)

    def signal_handler(signal, frame):
        info("\nShutting down proxy server")
        m.shutdown()
        success("Proxy server stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    m.run()
