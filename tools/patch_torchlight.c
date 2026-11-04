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

    // Embed strings at 0x7e6912 (VA 0xbe7712)
    // 1. "Desligado\0" (len 10) -> VA 0xbe7712
    // 2. "Apenas Iluminação\0" (len 20) -> VA 0xbe771c
    // 3. "Baixo\0" (len 6) -> VA 0xbe7730
    // 4. "Médio\0" (len 7) -> VA 0xbe7736
    // 5. "Alto\0" (len 5) -> VA 0xbe773d
    // 6. "Muito Alto\0" (len 11) -> VA 0xbe7742

    const unsigned int va_desligado = 0xbe7712;
    const unsigned int va_iluminacao = 0xbe771c;
    const unsigned int va_baixo = 0xbe7730;
    const unsigned int va_medio = 0xbe7736;
    const unsigned int va_alto = 0xbe773d;
    const unsigned int va_muito_alto = 0xbe7742;

    const char s_desligado[] = "Desligado";
    const char s_iluminacao[] = "Apenas Ilumina\xc3\xa7\xc3\xa3o";
    const char s_baixo[] = "Baixo";
    const char s_medio[] = "M\xc3\xa9" "dio";
    const char s_alto[] = "Alto";
    const char s_muito_alto[] = "Muito Alto";

    memcpy(buf + 0x7e6912, s_desligado, sizeof(s_desligado));
    memcpy(buf + 0x7e691c, s_iluminacao, sizeof(s_iluminacao));
    memcpy(buf + 0x7e6930, s_baixo, sizeof(s_baixo));
    memcpy(buf + 0x7e6936, s_medio, sizeof(s_medio));
    memcpy(buf + 0x7e693d, s_alto, sizeof(s_alto));
    memcpy(buf + 0x7e6942, s_muito_alto, sizeof(s_muito_alto));

    PatchEntry patches[] = {
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
            if (*pval == patches[i].orig_va || *pval == patches[i].new_va) {
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

    return 0;
}
