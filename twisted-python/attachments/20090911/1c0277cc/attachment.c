/*
  Windows 2000 XP API Wrapper Pack
  Copyright (C) 2008 OldCigarette

  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2.1 of the License, or (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this library; if not, write to the Free Software
  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
*/

#define _WIN32_WINNT 0x0500
#include <Winsock2.h>
#include <WS2tcpip.h>
#include <WSPiApi.h>
#include <MSWSock.h>
#include <windows.h>

#include "../common/win2k_xp_debug.h"
/*Debugging*/
int debugLevel;
DbgPrintf_t DbgPrintf;

GUID ConnectExGUID    = WSAID_CONNECTEX;
GUID DisconnectExGUID = WSAID_DISCONNECTEX;
GUID TransmitFileGUID = WSAID_TRANSMITFILE;

HANDLE hHeap = NULL;

#define MALLOC(x) HeapAlloc(hHeap, 0, x)
#define FREE(x) HeapFree(hHeap, 0, x)

typedef struct _CONNECTEX_CONNECT_DATA {
	SOCKET       s;
	PVOID        lpSendBuffer;
	DWORD        dwSendDataLength;
	LPOVERLAPPED lpOverlapped;
	WSAEVENT     event;
	HANDLE       WaitObject;
} CONNECTEX_CONNECT_DATA;

void FreeConnectData(CONNECTEX_CONNECT_DATA *data) {
	if(data->lpSendBuffer) FREE(data->lpSendBuffer);
	if(data->WaitObject) 
	if(data->event != WSA_INVALID_EVENT) WSACloseEvent(data->event);
	FREE(data);
}

BOOL CALLBACK ConnectEx_CONNECT (PVOID lpParameter, BOOLEAN TimerOrWaitFired) {
	fd_set fdset;
	WSABUF wsabuf;
	DWORD  sent, dwTemp;
	int r;
	BOOL ret = FALSE;
	CONNECTEX_CONNECT_DATA *data = (CONNECTEX_CONNECT_DATA *)lpParameter;
	
	if(data->WaitObject) UnregisterWait(data->WaitObject);
	
	//Do we have a connection?
	fdset.fd_count = 1;
	fdset.fd_array[0] = data->s;
	
	if(select(0, NULL, &fdset, NULL, NULL) == 1) {
		if(!data->lpSendBuffer) { ret = TRUE; goto cleanup; }
	
		//We are ready to send data
		wsabuf.len = data->dwSendDataLength;
		wsabuf.buf = data->lpSendBuffer;
		sent = 0;
		
		if(data->event == WSA_INVALID_EVENT) {
			//Blocking - will send everything
			r = WSASend(data->s, &wsabuf, 1, &sent, 0, NULL, NULL);
			if(r == SOCKET_ERROR && debugLevel)
				DbgPrintf(DBG_WARN, S_YELLOW "ws2_32: ConnectEx_CONNECT blocking send failed 0x%08X\n", WSAGetLastError());
		} else {
			r = WSAEventSelect(data->s, data->event, FD_WRITE);
			if(r == SOCKET_ERROR) {
				if(debugLevel)
					DbgPrintf(DBG_WARN, S_YELLOW "ws2_32: Could not connect event to FD_WRITE 0x%08X\n", WSAGetLastError());			
				goto cleanup;
			}
			
			while(r != SOCKET_ERROR) {
				r = WSASend(data->s, &wsabuf, 1, &dwTemp, 0, NULL, NULL);
								
				if(r == SOCKET_ERROR && debugLevel)
					DbgPrintf(DBG_WARN, S_YELLOW "ws2_32: ConnectEx_CONNECT blocking send failed 0x%08X\n", WSAGetLastError());
				
				sent += dwTemp;
				if(sent >= data->dwSendDataLength) { ret = TRUE; goto cleanup; }
			
				wsabuf.buf += dwTemp;
				wsabuf.len -= dwTemp;
				
				WaitForSingleObject(data->event, INFINITE);
			}
		}
	} else {
		if(debugLevel)
			DbgPrintf(DBG_WARN, S_YELLOW "ws2_32: ConnectEx_CONNECT socket is not ready\n");
	}
	
cleanup:
	if(data->lpOverlapped) WSASetEvent(data->lpOverlapped->hEvent);
	FreeConnectData(data);
	return ret;
}

CONNECTEX_CONNECT_DATA *CreateConnectData
  (SOCKET s, PVOID lpSendBuffer, DWORD dwSendDataLength, LPOVERLAPPED lpOverlapped, 
   WSAEVENT event) {
	CONNECTEX_CONNECT_DATA *data;
	data = (CONNECTEX_CONNECT_DATA *)MALLOC(sizeof(CONNECTEX_CONNECT_DATA));
	
	//Store the socket to send on
	data->s = s;
	
	//Copy the send buffer
	if(lpSendBuffer) {
		data->lpSendBuffer = (PVOID)MALLOC(dwSendDataLength);
		RtlCopyMemory(data->lpSendBuffer, lpSendBuffer, dwSendDataLength);
		data->dwSendDataLength = dwSendDataLength;
	} else {
		data->lpSendBuffer = NULL;
		data->dwSendDataLength = 0;
	}
	
	//Store the event we must close
	data->event = event;
	
	data->lpOverlapped = lpOverlapped;
	
	data->WaitObject = NULL;
	
	return data;
}

BOOL PASCAL XP_ConnectEx(SOCKET s, const struct sockaddr *name, int namelen,
  PVOID lpSendBuffer, DWORD dwSendDataLength, LPDWORD lpdwBytesSent,
  LPOVERLAPPED lpOverlapped) {
	int r;
	HANDLE h;
	BOOL ret;
	CONNECTEX_CONNECT_DATA *data;
	DWORD len = 0;
	WSAEVENT event = WSA_INVALID_EVENT;
	
	r = connect(s, name, namelen);
	if(r == SOCKET_ERROR) {
		if(WSAGetLastError() != WSAEWOULDBLOCK) return FALSE;
		//It's going to take us a bit to connect
		
		event = WSACreateEvent();
		if(event == WSA_INVALID_EVENT) {
			if(debugLevel)
				DbgPrintf(DBG_WARN, S_YELLOW "ws2_32: Could not create an event for ConnectEx 0x%08X\n", WSAGetLastError());
			return FALSE;
		}
		
		data = CreateConnectData(s, lpSendBuffer, dwSendDataLength, lpOverlapped, event);
		if(!RegisterWaitForSingleObject(&data->WaitObject, event, ConnectEx_CONNECT, data, INFINITE, WT_EXECUTEINIOTHREAD|WT_EXECUTEONLYONCE)) {
			if(debugLevel)
				DbgPrintf(DBG_WARN, S_YELLOW "ws2_32: Could not register event for ConnectEx 0x%08X\n", GetLastError());
			WSACloseEvent(event);
			FreeConnectData(data);
			return FALSE;
		}
		
		r = WSAEventSelect(s, event, FD_CONNECT);
		if(r == SOCKET_ERROR) {
			if(debugLevel)
				DbgPrintf(DBG_WARN, S_YELLOW "ws2_32: Could not connect event to FD_CONNECT 0x%08X\n", WSAGetLastError());
			WSACloseEvent(event);
			FreeConnectData(data);
			return FALSE;
		}
		
		WSASetLastError(ERROR_IO_PENDING);
		return FALSE;
	}
	
	data = CreateConnectData(s, lpSendBuffer, dwSendDataLength, lpOverlapped, WSA_INVALID_EVENT);
	ret = ConnectEx_CONNECT(data, FALSE);
	if(lpdwBytesSent) *lpdwBytesSent = dwSendDataLength;
	return ret;
}

/*http://www.microsoft.com/mspress/books/sampchap/5726.aspx
  However, for Windows 2000 or Windows NT 4.0 it is possible to call
  TransmitFile with a null filehandle and buffers but specify the disconnect 
  and re-use flags, which will achieve the same results.*/
BOOL PASCAL XP_DisconnectEx(SOCKET s, LPOVERLAPPED lpOverlapped, DWORD dwFlags, DWORD dwReserved) {
	LPFN_TRANSMITFILE _TransmitFile;
	int r;
	DWORD bytes, flags;
	
	r = WSAIoctl(s, SIO_GET_EXTENSION_FUNCTION_POINTER, &TransmitFileGUID, sizeof(GUID),
			&_TransmitFile, sizeof(LPFN_TRANSMITFILE), &bytes, NULL, NULL);
	
	if(r == SOCKET_ERROR) return FALSE;
	
	flags = TF_DISCONNECT;
	if(dwFlags & TF_REUSE_SOCKET) flags |= TF_REUSE_SOCKET;
	return _TransmitFile(s, NULL, 0, 0, lpOverlapped, NULL, flags);
}

int WSAAPI XP_WSAIoctl(SOCKET s, DWORD dwIoControlCode, LPVOID lpvInBuffer, DWORD cbInBuffer,
  LPVOID lpvOutBuffer, DWORD cbOutBuffer, LPDWORD lpcbBytesReturned, LPWSAOVERLAPPED lpOverlapped,
  LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine) {
	int r;
	
	r = WSAIoctl(s, dwIoControlCode, lpvInBuffer, cbInBuffer, lpvOutBuffer, cbOutBuffer,
			lpcbBytesReturned, lpOverlapped, lpCompletionRoutine);

	if(dwIoControlCode == SIO_GET_EXTENSION_FUNCTION_POINTER && 
	   lpvInBuffer &&
	   r == SOCKET_ERROR) {
		if(debugLevel) DbgPrintf(DBG_INFO, 
				"WSAIoctl SIO_GET_EXTENSION_FUNCTION_POINTER GUID=0x%08X\n",
				*(DWORD *)lpvInBuffer);
		if(memcmp(lpvInBuffer, &ConnectExGUID, sizeof(GUID)) == 0) {
			SetLastError(ERROR_SUCCESS);
			if(cbOutBuffer >= 4 && lpvOutBuffer)
				*(LPFN_CONNECTEX *)lpvOutBuffer = XP_ConnectEx;
			if(lpcbBytesReturned) *lpcbBytesReturned = 4;
			r = 0;
		} else if(memcmp(lpvInBuffer, &DisconnectExGUID, sizeof(GUID)) == 0) {
			SetLastError(ERROR_SUCCESS);
			if(cbOutBuffer >= 4 && lpvOutBuffer)
				*(LPFN_DISCONNECTEX *)lpvOutBuffer = XP_DisconnectEx;
			if(lpcbBytesReturned) *lpcbBytesReturned = 4;
			r = 0;
		} else if(debugLevel) {
			DbgPrintf(DBG_ERROR, 
				S_RED "WSAIoctl SIO_GET_EXTENSION_FUNCTION_POINTER GUID=0x%08X failed, WSALastError=0x%08X\n",
				*(DWORD *)lpvInBuffer, WSAGetLastError());
		}
	}
	
	return r;
}

//Cheers to Microsoft for doing the hard work!!!!

int WINAPI XP_getaddrinfo(const char* nodename, const char* servname, const struct addrinfo* hints, struct addrinfo** res) {
	return WspiapiLegacyGetAddrInfo(nodename, servname, hints, res);
}

void WINAPI XP_freeaddrinfo(struct addrinfo* ai) {
	WspiapiLegacyFreeAddrInfo(ai);
}

int WINAPI XP_getnameinfo(const struct sockaddr FAR* sa, socklen_t salen, char FAR* host,
                       DWORD hostlen, char FAR* serv, DWORD servlen, int flags) {
	return WspiapiLegacyGetNameInfo(sa, salen, host, hostlen, serv, servlen, flags);		   
}

void WINAPI XP_FreeAddrInfoW(PADDRINFOW pAddrInfo) {
	//well you can't get anything yet
}

BOOL WINAPI DllMain(
  HINSTANCE hinstDLL,
  DWORD fdwReason,
  LPVOID lpvReserved) {
	DebugLevel_t DebugLevel;
	
  	switch(fdwReason) {
		case DLL_PROCESS_ATTACH:
			if(!hHeap) hHeap = GetProcessHeap();
			
			//Init debug data
			DbgPrintf = GetDbgPrintf();
			DebugLevel = GetDebugLevel();
			
			if(DebugLevel) debugLevel = DebugLevel();
			else           debugLevel = 0;
			
			if(DbgPrintf) DbgPrintf(DBG_ALWAYS, "ws2_32: WS2_32.DLL Wrapper Init\n");
			break;
	}
	
	return TRUE;
}
