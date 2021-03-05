import operator
from functools import reduce
from ..shtrih.commands import COMMANDS
import asyncio
from typing import Union





class ShtrihProto:

    ENQ = bytearray((0x05,))
    STX = bytearray((0x02,))
    ACK = bytearray((0x06,))
    NAK = bytearray((0x15,))
    PING = bytearray((0x00,))
   
   
    @classmethod
    def crc_calc(cls, payload:bytearray) -> bytearray:
        """crc_calc [summary]

        [extended_summary]

        Args:
            payload (bytearray): [description]

        Returns:
            bytearray: [description]
        """
        return bytearray(reduce(operator.xor, payload))


    @classmethod
    async def handle(cls, payload:bytearray) -> Union[bytearray, None]:
        """process [summary]

        [extended_summary]

        Args:
            payload (bytearray): [description]
        """
        cmd = payload[0:1]
        if cmd == bytearray(0xFF):
            cmd = payload[0:2]
        cmd_handler = next((cmd for cmd in COMMANDS if cmd._command_code == cmd), None)
        if cmd_handler:
            output = cls.STX
            output.extend(cmd_handler.handle())
            output.extend(cls.crc_calc(output))
            return output
        else:
            return None
       




   
           
        


           

   


 


   