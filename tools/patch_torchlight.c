#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "patch_class_data.h"

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

static void patch_cegui_base(const char* exe_path) {
    char dll_path[MAX_PATH];
    strncpy(dll_path, exe_path, sizeof(dll_path) - 1);
    dll_path[sizeof(dll_path) - 1] = '\0';

    char* last_slash = strrchr(dll_path, '\\');
    char* last_fwd = strrchr(dll_path, '/');
    if (last_fwd && (!last_slash || last_fwd > last_slash)) {
        last_slash = last_fwd;
    }

    if (last_slash) {
        strcpy(last_slash + 1, "CEGUIBase.dll");
    } else {
        strcpy(dll_path, "CEGUIBase.dll");
    }

    FILE* f = fopen(dll_path, "rb");
    if (!f) return;
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (fsize < 0x7b658 + 6) {
        fclose(f);
        return;
    }

    unsigned char* buf = (unsigned char*)malloc(fsize);
    if (!buf) {
        fclose(f);
        return;
    }

    if (fread(buf, 1, fsize, f) != (size_t)fsize) {
        free(buf);
        fclose(f);
        return;
    }
    fclose(f);

    const unsigned char orig_hook[6] = { 0x47, 0x46, 0x89, 0x7c, 0x24, 0x1c };
    const unsigned char patched_hook[6] = { 0xe9, 0x87, 0x0c, 0xfe, 0xff, 0x90 };
    const unsigned char cave_bytes[24] = {
        0x47, 0x46, 0x80, 0x3e, 0x80, 0x72, 0x08, 0x80,
        0x3e, 0xc0, 0x73, 0x03, 0x46, 0xeb, 0xf3, 0x89,
        0x7c, 0x24, 0x1c, 0xe9, 0x62, 0xf3, 0x01, 0x00
    };

    if (memcmp(buf + 0x7b658, orig_hook, 6) == 0 || memcmp(buf + 0x7b658, patched_hook, 6) == 0) {
        char backup_path[MAX_PATH];
        snprintf(backup_path, sizeof(backup_path), "%s.orig", dll_path);
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

        memcpy(buf + 0x7b658, patched_hook, 6);
        memcpy(buf + 0x5c2e4, cave_bytes, 24);

        f = fopen(dll_path, "wb");
        if (f) {
            fwrite(buf, 1, fsize, f);
            fclose(f);
        }
    }
    free(buf);
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
    const unsigned int va_dificuldade_colon = 0xa8092c;

    const char s_desligado[] = "Desligado";
    const char s_iluminacao[] = "Apenas Ilumina\xe7\xe3o";
    const char s_baixo[] = "Baixo";
    const char s_medio[] = "M\xe9" "dio";
    const char s_alto[] = "Alto";
    const char s_muito_alto[] = "Muito Alto";
    const wchar_t s_dica[] = L"Dica";
    const wchar_t s_dificuldade_colon[] = L"Dificuldade:";

    memset(buf + 0x7e6912, 0, 100);
    memcpy(buf + 0x7e6912, s_desligado, sizeof(s_desligado));
    memcpy(buf + 0x7e691c, s_iluminacao, sizeof(s_iluminacao));
    memcpy(buf + 0x7e692e, s_baixo, sizeof(s_baixo));
    memcpy(buf + 0x7e6934, s_medio, sizeof(s_medio));
    memcpy(buf + 0x7e693a, s_alto, sizeof(s_alto));
    memcpy(buf + 0x7e693f, s_muito_alto, sizeof(s_muito_alto));
    memcpy(buf + 0x7e694a, s_dica, sizeof(s_dica));

    // Embed L"Dificuldade:" in .rdata slack space at raw 0x67fb2c (VA 0xa8092c, 26 bytes)
    if (fsize > 0x67fb2c + (long)sizeof(s_dificuldade_colon)) {
        memcpy(buf + 0x67fb2c, s_dificuldade_colon, sizeof(s_dificuldade_colon));
    }

    // Character Creation screen (class names + descriptions).
    // Position independent hooks (Torchlight.exe uses ASLR), never touching bytes covered by
    // base relocations. All bytes come from tools/patch_class_data.h, generated by
    // `python tools/patch_torchlight_exe.py --emit-c tools/patch_class_data.h`
    // so this C patcher and the Python patcher can never diverge.
    int class_ok = 1;
    for (size_t i = 0; i < sizeof(class_anchor_raw) / sizeof(class_anchor_raw[0]); i++) {
        if ((long)(class_anchor_raw[i] + sizeof(class_anchor_bytes)) > fsize ||
            memcmp(buf + class_anchor_raw[i], class_anchor_bytes, sizeof(class_anchor_bytes)) != 0) {
            class_ok = 0;  // different Torchlight build: leave the class screen untouched
        }
    }
    if (class_ok) {
        // Heal executables patched by older (broken) revisions
        for (size_t i = 0; i < sizeof(class_restore) / sizeof(class_restore[0]); i++)
            memcpy(buf + class_restore[i].raw, class_restore[i].bytes, class_restore[i].len);
        for (size_t i = 0; i < sizeof(class_zero) / sizeof(class_zero[0]); i++)
            memset(buf + class_zero[i][0], 0, class_zero[i][1] - class_zero[i][0]);
        for (size_t i = 0; i < sizeof(class_writes) / sizeof(class_writes[0]); i++)
            memcpy(buf + class_writes[i].raw, class_writes[i].bytes, class_writes[i].len);
    }

    PatchEntry patches[] = {
        // TipMenu::init (0x5af740) - Modal Title "Tip" -> "Dica"
        { 0x1af76a, 0xa8fc0c, va_dica },

        // Journal/Diary screen (0x5819b5) - "Difficulty:" -> "Dificuldade:"
        { 0x180db5, 0xa8ec20, va_dificuldade_colon },

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
            if (*pval == patches[i].orig_va || *pval == patches[i].new_va || (*pval >= 0xbe7712 && *pval <= 0xbe7760)) {
                *pval = patches[i].new_va;
            }
        }
    }

    // In-place string patch: " Gold" -> " Ouro" for floating combat text
    // Raw 0x67bd84 (ASCII, 6 bytes): " Gold\0" -> " Ouro\0"
    if (fsize > 0x67bd84 + 6) {
        if (memcmp(buf + 0x67bd84, " Gold\0", 6) == 0 || memcmp(buf + 0x67bd84, " Ouro\0", 6) == 0) {
            memcpy(buf + 0x67bd84, " Ouro\0", 6);
        }
    }
    // Raw 0x67e854 (UTF-16LE, 12 bytes): L" Gold\0" -> L" Ouro\0"
    if (fsize > 0x67e854 + 12) {
        const wchar_t w_gold[] = L" Gold";
        const wchar_t w_ouro[] = L" Ouro";
        if (memcmp(buf + 0x67e854, w_gold, sizeof(w_gold)) == 0 || memcmp(buf + 0x67e854, w_ouro, sizeof(w_ouro)) == 0) {
            memcpy(buf + 0x67e854, w_ouro, sizeof(w_ouro));
        }
    }

    // Raw 0x668698 (UTF-16LE, 14 bytes): L"Floor \0" -> L"Andar \0" (Scenario entry overlay: e.g. "Minas de Orden" / "Andar 1")
    if (fsize > 0x668698 + 14) {
        const wchar_t w_floor[] = L"Floor ";
        const wchar_t w_andar[] = L"Andar ";
        if (memcmp(buf + 0x668698, w_floor, sizeof(w_floor)) == 0 || memcmp(buf + 0x668698, w_andar, sizeof(w_andar)) == 0) {
            memcpy(buf + 0x668698, w_andar, sizeof(w_andar));
        }
    }

    // Raw 0x6801f0 (UTF-16LE, 20 bytes): L" - Floor \0" -> L" - Andar \0"
    if (fsize > 0x6801f0 + 20) {
        const wchar_t w_dash_floor[] = L" - Floor ";
        const wchar_t w_dash_andar[] = L" - Andar ";
        if (memcmp(buf + 0x6801f0, w_dash_floor, sizeof(w_dash_floor)) == 0 || memcmp(buf + 0x6801f0, w_dash_andar, sizeof(w_dash_andar)) == 0) {
            memcpy(buf + 0x6801f0, w_dash_andar, sizeof(w_dash_andar));
        }
    }

    // Raw 0x68ddc8 (UTF-16LE, 24 bytes): L"Ancestors:\0\0" -> L"Ancestrais:\0" (Journal/Diary screen)
    if (fsize > 0x68ddc8 + 24) {
        const wchar_t w_ancestors[] = L"Ancestors:\0";
        const wchar_t w_ancestrais[] = L"Ancestrais:";
        if (memcmp(buf + 0x68ddc8, w_ancestors, 22) == 0 || memcmp(buf + 0x68ddc8, w_ancestrais, sizeof(w_ancestrais)) == 0) {
            memcpy(buf + 0x68ddc8, w_ancestrais, sizeof(w_ancestrais));
        }
    }

    // Raw 0x68ef2c (UTF-16LE, 24 bytes): L"Difficulty\0\0" -> L"Dificuldade\0"
    if (fsize > 0x68ef2c + 24) {
        const wchar_t w_difficulty[] = L"Difficulty\0";
        const wchar_t w_dificuldade[] = L"Dificuldade";
        if (memcmp(buf + 0x68ef2c, w_difficulty, 22) == 0 || memcmp(buf + 0x68ef2c, w_dificuldade, sizeof(w_dificuldade)) == 0) {
            memcpy(buf + 0x68ef2c, w_dificuldade, sizeof(w_dificuldade));
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

    // Patch CEGUIBase.dll with UTF-8 synchronization hook to support diacritics in color tags
    patch_cegui_base(exe_path);

    // Optimize local_settings.txt so Torchlight launches in native resolution and Fullscreen
    optimize_display_settings();

    return 0;
}
