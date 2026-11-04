#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SLACK_RAW_START 0x7e6912
#define SLACK_VA_START  0xbe7712

typedef struct {
    unsigned int raw_offset;
    unsigned int orig_va;
    unsigned int new_va;
} PatchEntry;

static void optimize_display_settings(void) {
    typedef BOOL (WINAPI *SetProcessDPIAwareFn)(void);
    HMODULE hUser32 = LoadLibraryA("user32.dll");
    if (hUser32) {
        SetProcessDPIAwareFn pSetDPI = (SetProcessDPIAwareFn)GetProcAddress(hUser32, "SetProcessDPIAware");
        if (pSetDPI) {
            pSetDPI();
        }
    }

    int screen_w = GetSystemMetrics(SM_CXSCREEN);
    int screen_h = GetSystemMetrics(SM_CYSCREEN);
    if (hUser32) FreeLibrary(hUser32);

    if (screen_w < 800 || screen_h < 600) {
        screen_w = 1024;
        screen_h = 768;
    }

    char appdata[MAX_PATH];
    if (!GetEnvironmentVariableA("APPDATA", appdata, sizeof(appdata))) {
        return;
    }

    char folder[MAX_PATH];
    snprintf(folder, sizeof(folder), "%s\\runic games", appdata);
    CreateDirectoryA(folder, NULL);
    snprintf(folder, sizeof(folder), "%s\\runic games\\torchlight", appdata);
    CreateDirectoryA(folder, NULL);

    char settings_path[MAX_PATH];
    snprintf(settings_path, sizeof(settings_path), "%s\\local_settings.txt", folder);

    FILE* f = fopen(settings_path, "rb");
    if (!f) {
        // File does not exist yet: write clean default in UTF-16LE
        f = fopen(settings_path, "wb");
        if (!f) return;
        wchar_t wbuf[2048];
        int wlen = swprintf(wbuf, 2048,
            L"LEVEL_SEED :0\r\nOPENGL :0\r\nRENDERBEHIND :1\r\nFULLSCREEN :1\r\nRESTART_ON_FULLSCREEN_CHANGE :0\r\nRESTARTING :0\r\nFLOATY_NUMBERS :1\r\nVSYNCH :1\r\nWINDOW_WIDTH :%d\r\nWINDOW_HEIGHT :%d\r\nRES_WIDTH :%d\r\nRES_HEIGHT :%d\r\nMAX_FPS :200\r\nCURRENT FPS :60\r\nMAX_PARTICLES :5000\r\nSHADOWS_ENABLED :1\r\nSHADOWS_DETAIL :4\r\nRIMLIGHTS_ENABLED :1\r\nLIGHTING_ENABLED :1\r\nALLOW HWSKINNING :1\r\nMAX_RENDER_FPS :60\r\nVERSION :17685_201001261433\r\nZIP :Pak.zip\r\n",
            screen_w, screen_h, screen_w, screen_h);
        fwrite(wbuf, sizeof(wchar_t), wlen, f);
        fclose(f);
        return;
    }

    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (fsize <= 2) {
        fclose(f);
        return;
    }

    wchar_t* in_buf = (wchar_t*)malloc(fsize + 4);
    if (!in_buf) {
        fclose(f);
        return;
    }
    size_t r = fread(in_buf, 1, fsize, f);
    fclose(f);
    in_buf[r / sizeof(wchar_t)] = L'\0';

    wchar_t* out_buf = (wchar_t*)malloc((fsize + 2048) * sizeof(wchar_t));
    if (!out_buf) {
        free(in_buf);
        return;
    }
    out_buf[0] = L'\0';

    wchar_t* ctx = NULL;
    wchar_t* line = wcstok(in_buf, L"\r\n", &ctx);
    while (line) {
        wchar_t newline[512];
        if (wcsncmp(line, L"FULLSCREEN :", 12) == 0) {
            swprintf(newline, 512, L"FULLSCREEN :1");
        } else if (wcsncmp(line, L"WINDOW_WIDTH :", 14) == 0) {
            swprintf(newline, 512, L"WINDOW_WIDTH :%d", screen_w);
        } else if (wcsncmp(line, L"WINDOW_HEIGHT :", 15) == 0) {
            swprintf(newline, 512, L"WINDOW_HEIGHT :%d", screen_h);
        } else if (wcsncmp(line, L"RES_WIDTH :", 11) == 0) {
            swprintf(newline, 512, L"RES_WIDTH :%d", screen_w);
        } else if (wcsncmp(line, L"RES_HEIGHT :", 12) == 0) {
            swprintf(newline, 512, L"RES_HEIGHT :%d", screen_h);
        } else {
            wcsncpy(newline, line, 511);
            newline[511] = L'\0';
        }
        wcscat(out_buf, newline);
        wcscat(out_buf, L"\r\n");
        line = wcstok(NULL, L"\r\n", &ctx);
    }

    f = fopen(settings_path, "wb");
    if (f) {
        fwrite(out_buf, sizeof(wchar_t), wcslen(out_buf), f);
        fclose(f);
    }

    free(in_buf);
    free(out_buf);
}

int main(int argc, char* argv[]) {
    char exe_path[MAX_PATH];
    if (argc > 1) {
        strncpy(exe_path, argv[1], MAX_PATH - 1);
        exe_path[MAX_PATH - 1] = '\0';
    } else {
        strcpy(exe_path, "Torchlight.exe");
    }

    FILE* f = fopen(exe_path, "rb");
    if (!f) {
        return 1;
    }
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (fsize < 0x7e6a00) {
        fclose(f);
        return 2;
    }

    unsigned char* buf = (unsigned char*)malloc(fsize);
    if (!buf) {
        fclose(f);
        return 3;
    }

    if (fread(buf, 1, fsize, f) != (size_t)fsize) {
        free(buf);
        fclose(f);
        return 4;
    }
    fclose(f);

    // Create backup if not already present
    char backup_path[MAX_PATH];
    snprintf(backup_path, sizeof(backup_path), "%s.orig", exe_path);
    FILE* fb = fopen(backup_path, "rb");
    if (!fb) {
        fb = fopen(backup_path, "wb");
        if (fb) {
            fwrite(buf, 1, fsize, fb);
            fclose(fb);
        }
    } else {
        fclose(fb);
    }

    // Embed strings at 0x7e6912 (VA 0xbe7712) in Windows-1252 / ISO-8859-1
    // (CEGUI String(const char*) zero-extends bytes to utf32 codepoints)
    // 1. "Desligado\0" (len 10) -> VA 0xbe7712
    // 2. "Apenas Iluminação\0" (len 18) -> VA 0xbe771c
    // 3. "Baixo\0" (len 6) -> VA 0xbe772e
    // 4. "Médio\0" (len 6) -> VA 0xbe7734
    // 5. "Alto\0" (len 5) -> VA 0xbe773a
    // 6. "Muito Alto\0" (len 11) -> VA 0xbe773f

    const unsigned int va_desligado = 0xbe7712;
    const unsigned int va_iluminacao = 0xbe771c;
    const unsigned int va_baixo = 0xbe772e;
    const unsigned int va_medio = 0xbe7734;
    const unsigned int va_alto = 0xbe773a;
    const unsigned int va_muito_alto = 0xbe773f;
    const unsigned int va_dica = 0xbe774a;

    const char s_desligado[] = "Desligado";
    const char s_iluminacao[] = "Apenas Ilumina\xe7\xe3o";
    const char s_baixo[] = "Baixo";
    const char s_medio[] = "M\xe9" "dio";
    const char s_alto[] = "Alto";
    const char s_muito_alto[] = "Muito Alto";
    const wchar_t s_dica[] = L"Dica";

    memset(buf + 0x7e6912, 0, 100);
    memcpy(buf + 0x7e6912, s_desligado, sizeof(s_desligado));
    memcpy(buf + 0x7e691c, s_iluminacao, sizeof(s_iluminacao));
    memcpy(buf + 0x7e692e, s_baixo, sizeof(s_baixo));
    memcpy(buf + 0x7e6934, s_medio, sizeof(s_medio));
    memcpy(buf + 0x7e693a, s_alto, sizeof(s_alto));
    memcpy(buf + 0x7e693f, s_muito_alto, sizeof(s_muito_alto));
    memcpy(buf + 0x7e694a, s_dica, sizeof(s_dica));

    // Character Creation screen localized descriptions:
    // Alchemist description at VA 0xbe7754 (raw 0x7e6954 in .rdata slack)
    const char s_desc_a[] = "O Alquimista canaliza o poder do \xc2mbar para atacar de longe e invocar lacaios.";
    memcpy(buf + 0x7e6954, s_desc_a, sizeof(s_desc_a));

    // Vanquisher description at VA 0xbe77a3 (raw 0x7e69a3 in .rdata slack)
    const char s_desc_v[] = "A Conquistadora \xe9 uma atiradora perita e usa armadilhas para debilitar seus inimigos.";
    memcpy(buf + 0x7e69a3, s_desc_v, sizeof(s_desc_v));

    // Destroyer description at VA 0xa5bd70 (raw 0x65b170 in .text slack)
    const char s_desc_d[] = "O Destruidor destaca-se no combate corpo a corpo e canaliza o poder dos seus ancestrais para derrotar seus inimigos.";
    memcpy(buf + 0x65b170, s_desc_d, sizeof(s_desc_d));

    // Assembly hooks in .text slack at 0x65b0c0 (VA 0xa5bcc0)
    // Hook 1: Localizes class name strings ("Destruidor", "Alquimista", "Conquistadora")
    // Hook 2: Intercepts class description calls and returns pointers to localized descriptions
    static const unsigned char hook_code[168] = {
        0xff, 0x74, 0x24, 0x08, 0xff, 0x74, 0x24, 0x08, 0xe8, 0x83, 0x00, 0xb7, 0xff, 0x83, 0xc4, 0x08,
        0x80, 0x38, 0x44, 0x75, 0x1d, 0xc7, 0x00, 0x44, 0x65, 0x73, 0x74, 0xc7, 0x40, 0x04, 0x72, 0x75,
        0x69, 0x64, 0x66, 0xc7, 0x40, 0x08, 0x72, 0x00, 0xc7, 0x40, 0x10, 0x0a, 0x00, 0x00, 0x00, 0xc3,
        0x80, 0x38, 0x41, 0x75, 0x1d, 0xc7, 0x00, 0x41, 0x6c, 0x71, 0x75, 0xc7, 0x40, 0x04, 0x69, 0x6d,
        0x69, 0x73, 0x66, 0xc7, 0x40, 0x08, 0x61, 0x00, 0xc7, 0x40, 0x10, 0x0a, 0x00, 0x00, 0x00, 0xc3,
        0x80, 0x38, 0x56, 0x75, 0x25, 0xc7, 0x00, 0x43, 0x6f, 0x6e, 0x71, 0xc7, 0x40, 0x04, 0x75, 0x69,
        0x73, 0x74, 0xc7, 0x40, 0x08, 0x61, 0x64, 0x6f, 0x72, 0x66, 0xc7, 0x40, 0x0c, 0x61, 0x00, 0xc7,
        0x40, 0x10, 0x0d, 0x00, 0x00, 0x00, 0xc3, 0xc3,
        0xff, 0x15, 0x90, 0xc3, 0xa5, 0x00, 0x80, 0x38, 0x54, 0x75, 0x2a, 0x80, 0x78, 0x04, 0x44, 0x75,
        0x08, 0xb8, 0x70, 0xbd, 0xa5, 0x00, 0xc3, 0x80, 0x78, 0x04, 0x41, 0x75, 0x08, 0xb8, 0x54, 0x77,
        0xbe, 0x00, 0xc3, 0x80, 0x78, 0x04, 0x56, 0x75, 0x08, 0xb8, 0xa3, 0x77, 0xbe, 0x00, 0xc3, 0xc3
    };
    memcpy(buf + 0x65b0c0, hook_code, sizeof(hook_code));

    // Patch call sites in CharacterCreate::update (0x5b6d10)
    // Site 1: 0x5b6d55 (file raw 0x1b6155) -> call 0xa5bcc0 (hook_class_name)
    const unsigned char site1_bytes[5] = { 0xe8, 0x66, 0x4f, 0x4a, 0x00 };
    memcpy(buf + 0x1b6155, site1_bytes, sizeof(site1_bytes));

    // Site 2: 0x5b6da9 (file raw 0x1b61a9) -> call 0xa5bcc0 (hook_class_name)
    const unsigned char site2_bytes[5] = { 0xe8, 0x12, 0x4f, 0x4a, 0x00 };
    memcpy(buf + 0x1b61a9, site2_bytes, sizeof(site2_bytes));

    // Site 3: 0x5b6e42 (file raw 0x1b6242) -> call 0xa5bd38 (hook_class_desc); push eax; nop
    const unsigned char site3_bytes[7] = { 0xe8, 0xf1, 0x4e, 0x4a, 0x00, 0x50, 0x90 };
    memcpy(buf + 0x1b6242, site3_bytes, sizeof(site3_bytes));

    PatchEntry patches[] = {
        // TipMenu::init (0x5af740) - Modal Title "Tip" -> "Dica"
        { 0x1af76a, 0xa8fc0c, va_dica },

        // SettingsMenu::static_init (0x9a1850)
        { 0x5a0c55, 0xa89a94, va_desligado },
        { 0x5a0c65, 0xa89a84, va_iluminacao },
        { 0x5a0c7d, 0xa89a80, va_baixo },
        { 0x5a0c92, 0xa89a78, va_medio },
        { 0x5a0ca7, 0xa89a70, va_alto },
        { 0x5a0cbc, 0xa89a64, va_muito_alto },
        { 0x5a0d05, 0xa89a80, va_baixo },
        { 0x5a0d15, 0xa89a78, va_medio },
        { 0x5a0d2d, 0xa89a70, va_alto },

        // TU1 static_init (0x9574b0)
        { 0x5568b5, 0xa89a94, va_desligado },
        { 0x5568c5, 0xa89a84, va_iluminacao },
        { 0x5568dd, 0xa89a80, va_baixo },
        { 0x5568f2, 0xa89a78, va_medio },
        { 0x556907, 0xa89a70, va_alto },
        { 0x55691c, 0xa89a64, va_muito_alto },
        { 0x556965, 0xa89a80, va_baixo },
        { 0x556975, 0xa89a78, va_medio },
        { 0x55698d, 0xa89a70, va_alto },

        // TU3 static_init (0xa27f20)
        { 0x627325, 0xa89a94, va_desligado },
        { 0x627335, 0xa89a84, va_iluminacao },
        { 0x62734d, 0xa89a80, va_baixo },
        { 0x627362, 0xa89a78, va_medio },
        { 0x627377, 0xa89a70, va_alto },
        { 0x62738c, 0xa89a64, va_muito_alto },
        { 0x6273e5, 0xa89a80, va_baixo },
        { 0x6273f5, 0xa89a78, va_medio },
        { 0x62740d, 0xa89a70, va_alto },
    };

    int num_patches = sizeof(patches) / sizeof(patches[0]);
    for (int i = 0; i < num_patches; i++) {
        unsigned int off = patches[i].raw_offset;
        if (buf[off] == 0x68) {
            unsigned int* pval = (unsigned int*)(buf + off + 1);
            if (*pval == patches[i].orig_va || (*pval >= 0xbe7712 && *pval <= 0xbe7760)) {
                *pval = patches[i].new_va;
            }
        }
    }

    f = fopen(exe_path, "wb");
    if (!f) {
        free(buf);
        return 5;
    }
    fwrite(buf, 1, fsize, f);
    fclose(f);
    free(buf);

    // Optimize local_settings.txt so Torchlight launches in native resolution and Fullscreen
    optimize_display_settings();

    return 0;
}
