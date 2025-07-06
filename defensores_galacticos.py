import pygame
import random
import math

pygame.init()
pygame.mixer.init()

canal_tiro = pygame.mixer.Channel(0)

LARGURA_TELA = 800
ALTURA_TELA = 600
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Defensores Galácticos")

# --- CORES ---
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 0, 0)
AZUL = (0, 0, 255)
CINZA = (100, 100, 100)
VERDE = (0, 200, 0)
LARANJA = (255, 165, 0)

# --- CONSTANTES DO JOGO ---
PERCENTUAL_PONTOS_FINAL = 0.80
CHANCE_SPAWN_FINAL = 0.25
MAX_VIDAS = 5
INTERVALO_FIXO_SPAWN_CORACAO = 15000 # Coração aparece a cada 15 segundos.

# --- CARREGAMENTO DE RECURSOS ---
try:
    nave_img = pygame.image.load('images/nave.png').convert_alpha()
    ovni_img = pygame.image.load('images/ovni.png').convert_alpha()
    asteroide_img = pygame.image.load('images/asteroides.png').convert_alpha()
    laser_img = pygame.image.load('images/laser.png').convert_alpha()
    fundo_espaco_img = pygame.image.load('images/fundo_espaco.png').convert()
    coracao_img = pygame.image.load('images/coracao.png').convert_alpha()
    
    som_vida_extra = pygame.mixer.Sound('sounds/vida_extra.mp3')
    som_vitoria = pygame.mixer.Sound('sounds/vitoria.mp3')
    som_tiro = pygame.mixer.Sound('sounds/laser.mp3')
    som_explosao_inimigo = pygame.mixer.Sound('sounds/explosao.mp3')
    som_dano_nave = pygame.mixer.Sound('sounds/explosao.mp3')
    som_game_over = pygame.mixer.Sound('sounds/Voicy_Game Over.mp3')
except pygame.error as e:
    print(f"Erro ao carregar recurso: {e}. Verifique os nomes dos arquivos e das pastas 'images' e 'sounds'.")
    pygame.quit()
    exit()

# --- REDIMENSIONAMENTO DE IMAGENS ---
nave_img = pygame.transform.scale(nave_img, (60, 60))
laser_img = pygame.transform.scale(laser_img, (10, 30))
ovni_img = pygame.transform.scale(ovni_img, (84, 60))
fundo_espaco_img = pygame.transform.scale(fundo_espaco_img, (LARGURA_TELA, ALTURA_TELA))
coracao_img = pygame.transform.scale(coracao_img, (40, 40))

# --- CONFIGURAÇÕES DE NÍVEIS ---
NIVEIS = {
    1: {"nome": "Fácil", "velocidade_inimigo": 0.4, "intervalo_spawn": 9000, "aumento_spawn": 3, "aumento_velocidade": 0.00001, "pontos_para_vencer": 250},
    2: {"nome": "Médio", "velocidade_inimigo": 0.5, "intervalo_spawn": 9000, "aumento_spawn": 3, "aumento_velocidade": 0.00002, "pontos_para_vencer": 300},
    3: {"nome": "Difícil", "velocidade_inimigo": 0.9, "intervalo_spawn": 7000, "aumento_spawn": 5, "aumento_velocidade": 0.00005, "pontos_para_vencer": 300},
}

# --- ESTADOS DO JOGO ---
ESTADO_TELA_INICIAL, ESTADO_TELA_INSTRUCOES, ESTADO_ESCOLHA_NIVEL = 0, 1, 2
ESTADO_JOGANDO, ESTADO_PAUSADO, ESTADO_GAME_OVER, ESTADO_VITORIA = 3, 4, 5, 6

estado_jogo = ESTADO_TELA_INICIAL
nivel_selecionado = 1

def desenhar_botao(texto, x, y, largura, altura, cor_botao, cor_texto, fonte, mouse_pos, clique_mouse):
    rect = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(tela, cor_botao, rect)
    pygame.draw.rect(tela, BRANCO, rect, 3)
    txt_surf = fonte.render(texto, True, cor_texto)
    txt_rect = txt_surf.get_rect(center=rect.center)
    tela.blit(txt_surf, txt_rect)
    if rect.collidepoint(mouse_pos) and clique_mouse:
        return True
    return False

def show_text(surf, text, size, x, y, color=BRANCO):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surf.blit(text_surface, text_rect)

# --- CLASSES DO JOGO ---
class Nave(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = nave_img
        self.rect = self.image.get_rect(centerx=LARGURA_TELA // 2, bottom=ALTURA_TELA - 10)
        self.vida = 3
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = 250

    def update(self):
        velocidade = 5
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]: self.rect.x -= velocidade
        if teclas[pygame.K_RIGHT]: self.rect.x += velocidade
        if teclas[pygame.K_UP]: self.rect.y -= velocidade
        if teclas[pygame.K_DOWN]: self.rect.y += velocidade
        self.rect.clamp_ip(tela.get_rect())

    def atirar(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            laser = Laser(self.rect.centerx, self.rect.top)
            todos_sprites.add(laser)
            lasers.add(laser)
            canal_tiro.play(som_tiro)

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = laser_img
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.velocidade_y = -10

    def update(self):
        self.rect.y += self.velocidade_y
        if self.rect.bottom < 0:
            self.kill()

class Inimigo(pygame.sprite.Sprite):
    def __init__(self, imagem, pontos):
        super().__init__()
        self.image = imagem
        self.rect = self.image.get_rect(
            x=random.randrange(LARGURA_TELA - self.image.get_width()),
            y=random.randrange(-150, -100)
        )
        self.velocidade_x = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        self.velocidade_y = random.uniform(1.0, 3.0)
        self.pontos = pontos

    def update(self):
        self.rect.x += self.velocidade_x * velocidade_inimigo_atual
        self.rect.y += self.velocidade_y * velocidade_inimigo_atual
        if self.rect.left < 0 or self.rect.right > LARGURA_TELA:
            self.velocidade_x *= -1

class Coracao(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = coracao_img
        self.rect = self.image.get_rect(
            x=random.randrange(LARGURA_TELA - self.image.get_width()),
            y=random.randrange(-200, -150)
        )
        self.velocidade_y = 2 

    def update(self):
        self.rect.y += self.velocidade_y
        if self.rect.top > ALTURA_TELA:
            self.kill() 

# --- FUNÇÕES DO JOGO ---
def spawn_inimigo():
    if len(asteroides_grupo) + len(ovnis_grupo) < 10:
        if random.random() > 0.5:
            inimigo = Inimigo(pygame.transform.scale(asteroide_img, (70, 70)), 10)
            asteroides_grupo.add(inimigo)
        else:
            inimigo = Inimigo(ovni_img, 25)
            ovnis_grupo.add(inimigo)
        todos_sprites.add(inimigo)

def spawn_coracao():
    coracao = Coracao()
    todos_sprites.add(coracao)
    coracoes_grupo.add(coracao)

def reiniciar_jogo():
    global pontuacao, som_tocado_game_over, som_tocado_vitoria, jogador, modo_final_ativado, last_spawn_time, last_spawn_time_coracao
    pontuacao = 0
    som_tocado_game_over = False
    som_tocado_vitoria = False 
    modo_final_ativado = False
    
    todos_sprites.empty()
    lasers.empty()
    asteroides_grupo.empty()
    ovnis_grupo.empty()
    coracoes_grupo.empty() 
    
    jogador = Nave()
    todos_sprites.add(jogador)
    
    now = pygame.time.get_ticks()
    last_spawn_time = now
    last_spawn_time_coracao = now

    for _ in range(2):
        spawn_inimigo()

# --- INICIALIZAÇÃO DE VARIÁVEIS ---
fonte_botao = pygame.font.Font(None, 40)
pontuacao = 0
som_tocado_game_over = False
som_tocado_vitoria = False 
modo_final_ativado = False

todos_sprites = pygame.sprite.Group()
lasers = pygame.sprite.Group()
asteroides_grupo = pygame.sprite.Group()
ovnis_grupo = pygame.sprite.Group()
coracoes_grupo = pygame.sprite.Group()
jogador = None

clock = pygame.time.Clock()
rodando = True

# Temporizadores de Spawn
intervalo_spawn_inimigos, velocidade_aumento_spawn = 5000, 10
last_spawn_time = 0 
last_spawn_time_coracao = 0 

# Variáveis de Nível
velocidade_inimigo_atual, aumento_velocidade_inimigo = 0.2, 0.00005

# --- LOOP PRINCIPAL DO JOGO ---
while rodando:
    clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()
    clique_mouse = False

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            clique_mouse = True
        if evento.type == pygame.KEYDOWN:
            if estado_jogo == ESTADO_JOGANDO and jogador:
                if evento.key == pygame.K_SPACE:
                    jogador.atirar()
                if evento.key == pygame.K_p:
                    estado_jogo = ESTADO_PAUSADO
            if evento.key == pygame.K_ESCAPE:
                estado_jogo = ESTADO_TELA_INICIAL

    tela.blit(fundo_espaco_img, (0, 0))

    if estado_jogo == ESTADO_TELA_INICIAL:
        show_text(tela, "DEFENSORES GALÁCTICOS", 70, LARGURA_TELA//2, 150, AZUL)
        if desenhar_botao("Iniciar", LARGURA_TELA//2 - 100, 300, 200, 60, VERDE, PRETO, fonte_botao, mouse_pos, clique_mouse):
            estado_jogo = ESTADO_ESCOLHA_NIVEL
        if desenhar_botao("Instruções", LARGURA_TELA//2 - 100, 400, 200, 60, CINZA, PRETO, fonte_botao, mouse_pos, clique_mouse):
            estado_jogo = ESTADO_TELA_INSTRUCOES

    elif estado_jogo == ESTADO_TELA_INSTRUCOES:
        show_text(tela, "INSTRUÇÕES", 60, LARGURA_TELA//2, 100, AZUL)
        instrucoes = ["Setas: mover a nave", "Espaço: atirar", "P: pausar o jogo", "ESC: voltar ao menu"]
        for i, linha in enumerate(instrucoes):
            show_text(tela, linha, 32, LARGURA_TELA//2, 200 + i*40)
        if desenhar_botao("Voltar", LARGURA_TELA//2 - 100, 500, 200, 60, CINZA, PRETO, fonte_botao, mouse_pos, clique_mouse):
            estado_jogo = ESTADO_TELA_INICIAL

    elif estado_jogo == ESTADO_ESCOLHA_NIVEL:
        show_text(tela, "Escolha o nível de dificuldade", 50, LARGURA_TELA//2, 100, AZUL)
        largura_btn, altura_btn, espacamento, base_y = 180, 60, 20, 200
        pos_x = LARGURA_TELA//2 - largura_btn//2
        
        def iniciar_nivel(nivel):
            global nivel_selecionado, estado_jogo, intervalo_spawn_inimigos, velocidade_inimigo_atual, aumento_velocidade_inimigo, velocidade_aumento_spawn
            nivel_selecionado = nivel
            config = NIVEIS[nivel_selecionado]
            intervalo_spawn_inimigos = config["intervalo_spawn"]
            velocidade_inimigo_atual = config["velocidade_inimigo"]
            aumento_velocidade_inimigo = config["aumento_velocidade"]
            velocidade_aumento_spawn = config["aumento_spawn"]
            reiniciar_jogo()
            estado_jogo = ESTADO_JOGANDO

        if desenhar_botao("Fácil", pos_x, base_y, largura_btn, altura_btn, VERDE, PRETO, fonte_botao, mouse_pos, clique_mouse): iniciar_nivel(1)
        if desenhar_botao("Médio", pos_x, base_y + altura_btn + espacamento, largura_btn, altura_btn, LARANJA, PRETO, fonte_botao, mouse_pos, clique_mouse): iniciar_nivel(2)
        if desenhar_botao("Difícil", pos_x, base_y + 2*(altura_btn + espacamento), largura_btn, altura_btn, VERMELHO, PRETO, fonte_botao, mouse_pos, clique_mouse): iniciar_nivel(3)
        if desenhar_botao("Voltar", pos_x, base_y + 3*(altura_btn + espacamento) + 20, largura_btn, altura_btn, CINZA, PRETO, fonte_botao, mouse_pos, clique_mouse): estado_jogo = ESTADO_TELA_INICIAL

    elif estado_jogo == ESTADO_JOGANDO:
        if jogador:
            velocidade_inimigo_atual += aumento_velocidade_inimigo
            todos_sprites.update()
            
            pontos_vitoria = NIVEIS[nivel_selecionado]["pontos_para_vencer"]
            if not modo_final_ativado and pontuacao >= pontos_vitoria * PERCENTUAL_PONTOS_FINAL:
                modo_final_ativado = True

            now = pygame.time.get_ticks()
            
            # Temporizador para spawn de inimigos
            if now - last_spawn_time > intervalo_spawn_inimigos:
                last_spawn_time = now
                if not modo_final_ativado:
                    spawn_inimigo()
                else:
                    if random.random() < CHANCE_SPAWN_FINAL:
                        spawn_inimigo()
            
            # Lógica de spawn do coração com temporizador fixo
            if nivel_selecionado in [2, 3] and jogador.vida < MAX_VIDAS:
                if now - last_spawn_time_coracao > INTERVALO_FIXO_SPAWN_CORACAO:
                    last_spawn_time_coracao = now
                    spawn_coracao()

            # --- VERIFICAÇÃO DE COLISÕES ---
            for grupo_inimigo in [asteroides_grupo, ovnis_grupo]:
                colisoes_tiros = pygame.sprite.groupcollide(lasers, grupo_inimigo, True, True)
                for inimigo in colisoes_tiros.values():
                    pontuacao += inimigo[0].pontos
                    som_explosao_inimigo.play()
                    spawn_inimigo()

            inimigos_colididos = pygame.sprite.spritecollide(jogador, asteroides_grupo, True) + pygame.sprite.spritecollide(jogador, ovnis_grupo, True)
            if inimigos_colididos:
                jogador.vida -= len(inimigos_colididos)
                som_dano_nave.play()
                spawn_inimigo()
            
            colisoes_coracao = pygame.sprite.spritecollide(jogador, coracoes_grupo, True)
            if colisoes_coracao:
                if jogador.vida < MAX_VIDAS:
                    jogador.vida += 1
                    som_vida_extra.play()

            for inimigo in list(asteroides_grupo) + list(ovnis_grupo):
                if inimigo.rect.top > ALTURA_TELA:
                    jogador.vida -= 1
                    som_dano_nave.play()
                    inimigo.kill()
            
            # --- VERIFICAÇÃO DE ESTADO DO JOGO ---
            if jogador.vida <= 0 and estado_jogo == ESTADO_JOGANDO:
                estado_jogo = ESTADO_GAME_OVER
                if not som_tocado_game_over:
                    som_game_over.play()
                    som_tocado_game_over = True
            
            elif pontuacao >= pontos_vitoria:
                estado_jogo = ESTADO_VITORIA

            # --- DESENHO NA TELA ---
            todos_sprites.draw(tela)
            show_text(tela, f"Pontuação: {pontuacao}", 25, LARGURA_TELA // 2, 20)
            show_text(tela, f"Vida: {jogador.vida}", 25, LARGURA_TELA - 60, 20)
            if desenhar_botao("Menu", 10, 10, 80, 40, CINZA, PRETO, fonte_botao, mouse_pos, clique_mouse):
                estado_jogo = ESTADO_TELA_INICIAL

    elif estado_jogo in [ESTADO_PAUSADO, ESTADO_GAME_OVER, ESTADO_VITORIA]:
        todos_sprites.draw(tela)
        
        if estado_jogo == ESTADO_PAUSADO:
            show_text(tela, "PAUSADO", 70, LARGURA_TELA // 2, ALTURA_TELA // 2 - 80, AZUL)
            if desenhar_botao("Continuar", LARGURA_TELA//2 - 100, ALTURA_TELA//2 - 20, 200, 60, VERDE, PRETO, fonte_botao, mouse_pos, clique_mouse): estado_jogo = ESTADO_JOGANDO
            if desenhar_botao("Menu Inicial", LARGURA_TELA//2 - 100, ALTURA_TELA//2 + 60, 200, 60, CINZA, PRETO, fonte_botao, mouse_pos, clique_mouse): estado_jogo = ESTADO_TELA_INICIAL
        
        elif estado_jogo == ESTADO_GAME_OVER:
            show_text(tela, "GAME OVER!", 74, LARGURA_TELA // 2, ALTURA_TELA // 2 - 50, VERMELHO)
            if desenhar_botao("Reiniciar", LARGURA_TELA//2 - 100, ALTURA_TELA//2 + 20, 200, 60, VERDE, PRETO, fonte_botao, mouse_pos, clique_mouse): iniciar_nivel(nivel_selecionado)
            if desenhar_botao("Menu Inicial", LARGURA_TELA//2 - 100, ALTURA_TELA//2 + 100, 200, 60, CINZA, PRETO, fonte_botao, mouse_pos, clique_mouse): estado_jogo = ESTADO_TELA_INICIAL

        elif estado_jogo == ESTADO_VITORIA:
            if not som_tocado_vitoria:
                pygame.mixer.stop()
                som_vitoria.play()
                som_tocado_vitoria = True
            
            show_text(tela, "VOCÊ VENCEU!", 74, LARGURA_TELA // 2, ALTURA_TELA // 2 - 50, VERDE)
            show_text(tela, f"Pontuação Final: {pontuacao}", 30, LARGURA_TELA // 2, ALTURA_TELA // 2 + 10)
            if desenhar_botao("Jogar de Novo", LARGURA_TELA//2 - 125, ALTURA_TELA//2 + 60, 250, 60, VERDE, PRETO, fonte_botao, mouse_pos, clique_mouse): iniciar_nivel(nivel_selecionado)
            if desenhar_botao("Menu Inicial", LARGURA_TELA//2 - 125, ALTURA_TELA//2 + 140, 250, 60, CINZA, PRETO, fonte_botao, mouse_pos, clique_mouse): estado_jogo = ESTADO_TELA_INICIAL

    pygame.display.flip()

pygame.quit()