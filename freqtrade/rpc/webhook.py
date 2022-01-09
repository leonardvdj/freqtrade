"""
This module manages webhook communication
"""
import logging
import time
from typing import Any, Dict

from requests import RequestException, post

from freqtrade.enums import RPCMessageType
from freqtrade.rpc import RPC, RPCHandler


logger = logging.getLogger(__name__)

logger.debug('Included module rpc.webhook ...')


class Webhook(RPCHandler):
    """  This class handles all webhook communication """

    def __init__(self, rpc: RPC, config: Dict[str, Any]) -> None:
        """
        Init the Webhook class, and init the super class RPCHandler
        :param rpc: instance of RPC Helper class
        :param config: Configuration object
        :return: None
        """
        super().__init__(rpc, config)

        self._url = self._config['webhook']['url']
        self._format = self._config['webhook'].get('format', 'form')
        self._retries = self._config['webhook'].get('retries', 0)
        self._retry_delay = self._config['webhook'].get('retry_delay', 0.1)

    def cleanup(self) -> None:
        """
        Cleanup pending module resources.
        This will do nothing for webhooks, they will simply not be called anymore
        """
        pass

    def send_msg(self, msg: Dict[str, Any]) -> None:
        """ Send a message to telegram channel """
        try:

            if msg['type'] == RPCMessageType.BUY:
                valuedict = self._config['webhook'].get('webhookbuy', None)

                msg['total_stake'] = "{stake_amount} {stake_currency}".format(**msg)
                if (self._rpc._fiat_converter):
                    msg['total_fiat_amount'] = self._rpc._fiat_converter.convert_amount(
                        msg['stake_amount'], msg['stake_currency'], msg['fiat_currency'])
                    msg['total_fiat'] = ', {total_fiat_amount} {fiat_currency}'.format(**msg)
                else:
                    msg['total_fiat'] = ''

            elif msg['type'] == RPCMessageType.BUY_CANCEL:
                valuedict = self._config['webhook'].get('webhookbuycancel', None)
            elif msg['type'] == RPCMessageType.BUY_FILL:
                valuedict = self._config['webhook'].get('webhookbuyfill', None)
            elif msg['type'] == RPCMessageType.SELL:
                valuedict = self._config['webhook'].get('webhooksell', None)

                msg['duration'] = msg['close_date'].replace(
                    microsecond=0) - msg['open_date'].replace(microsecond=0)
                msg['duration_min'] = msg['duration'].total_seconds() / 60

                msg['emoji'] = self._get_sell_emoji(msg)

                if (all(prop in msg for prop in ['gain', 'fiat_currency', 'stake_currency'])
                        and self._rpc._fiat_converter):
                    msg['profit_fiat'] = self._rpc._fiat_converter.convert_amount(
                        msg['profit_amount'], msg['stake_currency'], msg['fiat_currency'])
                    msg['profit_extra'] = (' ({gain}: {profit_amount:.8f} {stake_currency}'
                                           ' / {profit_fiat:.3f} {fiat_currency})').format(**msg)
                else:
                    msg['profit_extra'] = ''
            elif msg['type'] == RPCMessageType.SELL_FILL:
                valuedict = self._config['webhook'].get('webhooksellfill', None)
            elif msg['type'] == RPCMessageType.SELL_CANCEL:
                valuedict = self._config['webhook'].get('webhooksellcancel', None)
            elif msg['type'] in (RPCMessageType.STATUS,
                                 RPCMessageType.STARTUP,
                                 RPCMessageType.WARNING):
                valuedict = self._config['webhook'].get('webhookstatus', None)
            else:
                raise NotImplementedError('Unknown message type: {}'.format(msg['type']))
            if not valuedict:
                logger.info("Message type '%s' not configured for webhooks", msg['type'])
                return

            payload = {key: value.format(**msg) for (key, value) in valuedict.items()}
            self._send_msg(payload)
        except KeyError as exc:
            logger.exception("Problem calling Webhook. Please check your webhook configuration. "
                             "Exception: %s", exc)

    def _get_sell_emoji(self, msg):
        """
        Get emoji for sell-side
        """

        if float(msg['profit_ratio']) >= 0.05:
            return "\N{ROCKET}"
        elif float(msg['profit_ratio']) >= 0.0:
            return "\N{EIGHT SPOKED ASTERISK}"
        elif msg['sell_reason'] == "stop_loss":
            return"\N{WARNING SIGN}"
        else:
            return "\N{CROSS MARK}"

    def _send_msg(self, payload: dict) -> None:
        """do the actual call to the webhook"""

        success = False
        attempts = 0
        while not success and attempts <= self._retries:
            if attempts:
                if self._retry_delay:
                    time.sleep(self._retry_delay)
                logger.info("Retrying webhook...")

            attempts += 1

            try:
                if self._format == 'form':
                    response = post(self._url, data=payload)
                elif self._format == 'json':
                    response = post(self._url, json=payload)
                elif self._format == 'raw':
                    response = post(self._url, data=payload['data'],
                                    headers={'Content-Type': 'text/plain'})
                else:
                    raise NotImplementedError('Unknown format: {}'.format(self._format))

                # Throw a RequestException if the post was not successful
                response.raise_for_status()
                success = True

            except RequestException as exc:
                logger.warning("Could not call webhook url. Exception: %s", exc)
