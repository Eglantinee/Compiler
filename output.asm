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
zero_div_msg db 'zero division', 0
buff        db 11 dup(?)
.code
main:
	xor eax, eax
	xor ebx, ebx
	xor ecx, ecx
	push ebp
	mov ebp, esp
	sub esp, 4
	mov eax, 22
	push eax
	mov eax, 11
	push eax
	pop ecx
	pop eax
	mul ecx
	push eax
	mov eax, 22
	push eax
	pop ecx
	cmp ecx, 0
	je error
	pop eax
	cdq
	idiv ecx
	push eax
	mov eax, 3
	push eax
	mov eax, 3
	push eax
	pop ecx
	pop eax
	xor eax, ecx
	push eax
	pop eax
	cmp eax, 0
	sete al
	push eax
	pop ecx
	cmp ecx, 0
	je error
	pop eax
	cdq
	idiv ecx
	push eax
	pop eax
	mov dword ptr [ebp - 4], eax
	mov ebx, [ebp - 4]
	mov esp, ebp
	pop ebp
invoke  NumbToStr, ebx, ADDR buff
invoke  StdOut,eax
invoke  ExitProcess, 0

error:
	invoke StdOut, addr zero_div_msg
	invoke ExitProcess, 1

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