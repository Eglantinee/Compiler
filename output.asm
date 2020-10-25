.386
.model flat,stdcall
option casemap:none
include     D:\masm32\include\windows.inc
include     D:\masm32\include\kernel32.inc
include     D:\masm32\include\masm32.inc
includelib    D:\masm32\lib\kernel32.lib
includelib    D:\masm32\lib\masm32.lib
NumbToStr    PROTO: DWORD,:DWORD
.data
buff        db 11 dup(?)
.code
main:
	xor eax, eax
	xor ebx, ebx
	xor ecx, ecx
	sub esp, 4
	sub esp, 4
	push 21
	pop eax
	mov dword ptr [ebp - 8], eax
	mov eax, [ebp - 8]
	push eax
	mov eax, 5
	push eax
	mov eax, 111
	push eax
	pop ecx
	pop eax
	mul ecx
	push eax
	pop ecx
	pop eax
	mul ecx
	push eax
	mov ebx, [ebp - 8]
invoke  NumbToStr, ebx, ADDR buff
invoke  StdOut,eax
invoke  ExitProcess, 0
NumbToStr PROC uses ebx x:DWORD, buffer:DWORD
    mov     ecx, buffer
    mov     eax, x
    mov     ebx, 10
    add     ecx, ebx
@@:
    xor     edx, edx
    div     ebx
    add     edx, 48              	
    mov     BYTE PTR [ecx],dl   	
    dec     ecx                 	
    test    eax, eax
    jnz     @b
    inc     ecx
    mov     eax, ecx
    ret
NumbToStr ENDP
END main