import random
import time
import pygame
from pgzero.actor import Actor
from pgzero.rect import Rect
import pgzrun

class AtorRedimensionado(Actor):
    def __init__(self, image, pos=None, anchor=None, scale=1.0, **kwargs):
        super().__init__(image, pos, anchor, **kwargs)
        if scale != 1.0:
            nova_largura = int(self.width * scale)
            nova_altura = int(self.height * scale)
            self._surf = pygame.transform.scale(self._surf, (nova_largura, nova_altura))
            self._update_pos()

WIDTH = 800
HEIGHT = 600

BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 0, 0)
AZUL = (0, 0, 255)
CINZA = (100, 100, 100)
VERDE = (0, 200, 0)
LARANJA = (255, 165, 0)
VERDE_CLARO = (100, 255, 100)

MAX_VIDAS = 5
INTERVALO_FIXO_SPAWN_CORACAO = 15.0

NIVEIS = {
    1: {"nome": "Facil", "velocidade_inimigo": 0.4, "intervalo_spawn": 4.0, "pontos_para_vencer": 250},
    2: {"nome": "Medio", "velocidade_inimigo": 0.5, "intervalo_spawn": 3.0, "pontos_para_vencer": 300},
    3: {"nome": "Dificil", "velocidade_inimigo": 0.9, "intervalo_spawn": 2.0, "pontos_para_vencer": 300},
}

ESTADO_TELA_INICIAL, ESTADO_TELA_MANUAL, ESTADO_ESCOLHA_NIVEL = 0, 1, 2
ESTADO_JOGANDO, ESTADO_PAUSADO, ESTADO_GAME_OVER, ESTADO_VITORIA = 3, 4, 5, 6

estado_jogo = ESTADO_TELA_INICIAL
nivel_selecionado = 1

pontuacao = 0
som_tocado_game_over = False
som_tocado_vitoria = False
modo_final_ativado = False
fundo_redimensionado = None

jogador = None
lasers = []
asteroides = []
ovnis = []
coracoes = []

last_spawn_time = 0
last_spawn_time_coracao = 0
velocidade_inimigo_atual = 0.2
intervalo_spawn_inimigos = 5.0
aumento_velocidade_inimigo = 0.00005

def reiniciar_jogo():
    global pontuacao, som_tocado_game_over, som_tocado_vitoria, jogador, modo_final_ativado
    global last_spawn_time, last_spawn_time_coracao, lasers, asteroides, ovnis, coracoes
    global velocidade_inimigo_atual, intervalo_spawn_inimigos, aumento_velocidade_inimigo
    global fundo_redimensionado

    if fundo_redimensionado is None:
        try:
            fundo_original = pygame.image.load('images/fundo_espaco.png').convert()
            fundo_redimensionado = pygame.transform.scale(fundo_original, (WIDTH, HEIGHT))
        except pygame.error:
            print("Erro ao carregar a imagem de fundo 'fundo_espaco.png'")
            fundo_redimensionado = None

    config = NIVEIS[nivel_selecionado]
    intervalo_spawn_inimigos = config["intervalo_spawn"]
    velocidade_inimigo_atual = config["velocidade_inimigo"]
    aumento_velocidade_inimigo = config.get("aumento_velocidade", 0.00001)

    pontuacao = 0
    som_tocado_game_over = False
    som_tocado_vitoria = False
    modo_final_ativado = False

    lasers = []
    asteroides = []
    ovnis = []
    coracoes = []

    jogador = AtorRedimensionado('nave', scale=0.15)
    jogador.x = WIDTH // 2
    jogador.y = 480
    jogador.vida = 3
    jogador.last_shot = 0
    jogador.shoot_delay = 0.25

    last_spawn_time = 0
    last_spawn_time_coracao = 0

    for _ in range(2):
        spawn_inimigo()

def spawn_inimigo():
    if len(asteroides) + len(ovnis) < 15:
        if random.random() > 0.5:
            inimigo = AtorRedimensionado('asteroides', scale=0.12)
            inimigo.pontos = 10
            asteroides.append(inimigo)
        else:
            inimigo = AtorRedimensionado('ovni', scale=0.2)
            inimigo.pontos = 25
            ovnis.append(inimigo)

        inimigo.x = random.randint(40, WIDTH - 40)
        inimigo.y = random.randint(-150, -100)
        inimigo.velocidade_x = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        inimigo.velocidade_y = random.uniform(1.0, 3.0)

def spawn_coracao():
    coracao = AtorRedimensionado('coracao', scale=0.1)
    coracao.x = random.randint(30, WIDTH - 30)
    coracao.y = random.randint(-200, -150)
    coracao.velocidade_y = 2
    coracoes.append(coracao)

def desenhar_botao(texto, rect, cor_botao, cor_texto, mouse_pos):
    cor_final = cor_botao
    if rect.collidepoint(mouse_pos):
        cor_final = VERDE_CLARO

    screen.draw.filled_rect(rect, cor_final)
    screen.draw.rect(rect, BRANCO)
    screen.draw.text(texto, center=rect.center, color=cor_texto, fontsize=32)

def draw():
    screen.clear()
    if fundo_redimensionado:
        screen.blit(fundo_redimensionado, (0, 30))
    else:
        screen.fill(PRETO)
        
    mouse_pos = pygame.mouse.get_pos()

    if estado_jogo == ESTADO_TELA_INICIAL:
        screen.draw.text("DEFENSORES GALACTICOS", center=(WIDTH // 2, 150), fontsize=70, color=AZUL, owidth=1.5, ocolor=BRANCO)
        desenhar_botao("Iniciar", Rect(WIDTH//2 - 100, 300, 200, 60), VERDE, PRETO, mouse_pos)
        desenhar_botao("Manual", Rect(WIDTH//2 - 100, 400, 200, 60), CINZA, PRETO, mouse_pos)
    elif estado_jogo == ESTADO_TELA_MANUAL:
        screen.draw.text("MANUAL", center=(WIDTH // 2, 100), fontsize=60, color=AZUL)
        instrucoes = ["Setas: mover a nave", "Espaco: atirar", "P: pausar o jogo", "ESC: voltar ao menu"]
        for i, linha in enumerate(instrucoes):
            screen.draw.text(linha, center=(WIDTH // 2, 200 + i * 40), fontsize=32)
        desenhar_botao("Voltar", Rect(WIDTH//2 - 100, 500, 200, 60), CINZA, PRETO, mouse_pos)
    elif estado_jogo == ESTADO_ESCOLHA_NIVEL:
        screen.draw.text("Escolha o nivel de dificuldade", center=(WIDTH // 2, 100), fontsize=50, color=AZUL)
        largura_btn, altura_btn, espacamento, base_y = 180, 60, 20, 200
        pos_x = WIDTH // 2 - largura_btn // 2
        desenhar_botao("Facil", Rect(pos_x, base_y, largura_btn, altura_btn), VERDE, PRETO, mouse_pos)
        desenhar_botao("Medio", Rect(pos_x, base_y + altura_btn + espacamento, largura_btn, altura_btn), LARANJA, PRETO, mouse_pos)
        desenhar_botao("Dificil", Rect(pos_x, base_y + 2 * (altura_btn + espacamento), largura_btn, altura_btn), VERMELHO, PRETO, mouse_pos)
        desenhar_botao("Voltar", Rect(pos_x, base_y + 3 * (altura_btn + espacamento) + 20, largura_btn, altura_btn), CINZA, PRETO, mouse_pos)
    elif estado_jogo in [ESTADO_JOGANDO, ESTADO_PAUSADO, ESTADO_GAME_OVER, ESTADO_VITORIA]:
        if jogador:
            jogador.draw()
        for l in lasers: l.draw()
        for a in asteroides: a.draw()
        for o in ovnis: o.draw()
        for c in coracoes: c.draw()
        
        screen.draw.text(f"Pontuacao: {pontuacao}", topleft=(10, 10), fontsize=25)
        screen.draw.text(f"Vida: {jogador.vida}", topright=(WIDTH - 10, 10), fontsize=25)

        if estado_jogo == ESTADO_PAUSADO:
            screen.draw.text("PAUSADO", center=(WIDTH // 2, HEIGHT // 2 - 80), fontsize=70, color=AZUL, owidth=1, ocolor=BRANCO)
            desenhar_botao("Continuar", Rect(WIDTH//2 - 100, HEIGHT//2 - 20, 200, 60), VERDE, PRETO, mouse_pos)
            desenhar_botao("Menu Inicial", Rect(WIDTH//2 - 100, HEIGHT//2 + 60, 200, 60), CINZA, PRETO, mouse_pos)
        elif estado_jogo == ESTADO_GAME_OVER:
            screen.draw.text("GAME OVER!", center=(WIDTH // 2, HEIGHT // 2 - 50), fontsize=74, color=VERMELHO, owidth=1.5, ocolor=BRANCO)
            desenhar_botao("Reiniciar", Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 200, 60), VERDE, PRETO, mouse_pos)
            desenhar_botao("Menu Inicial", Rect(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 60), CINZA, PRETO, mouse_pos)
        elif estado_jogo == ESTADO_VITORIA:
            screen.draw.text("VOCE VENCEU!", center=(WIDTH // 2, HEIGHT // 2 - 50), fontsize=74, color=VERDE, owidth=1.5, ocolor=BRANCO)
            screen.draw.text(f"Pontuacao Final: {pontuacao}", center=(WIDTH // 2, HEIGHT // 2 + 20), fontsize=30)
            desenhar_botao("Jogar de Novo", Rect(WIDTH//2 - 125, HEIGHT//2 + 70, 250, 60), VERDE, PRETO, mouse_pos)
            desenhar_botao("Menu Inicial", Rect(WIDTH//2 - 125, HEIGHT//2 + 150, 250, 60), CINZA, PRETO, mouse_pos)

def update(dt):
    global velocidade_inimigo_atual, last_spawn_time, last_spawn_time_coracao, estado_jogo, pontuacao, modo_final_ativado, som_tocado_game_over, som_tocado_vitoria

    if estado_jogo != ESTADO_JOGANDO or not jogador:
        return

    velocidade_inimigo_atual += aumento_velocidade_inimigo * dt

    velocidade_nave = 5
    if keyboard.left: jogador.x -= velocidade_nave
    if keyboard.right: jogador.x += velocidade_nave
    if keyboard.up: jogador.y -= velocidade_nave
    if keyboard.down: jogador.y += velocidade_nave
    
    if jogador.left < 0:
        jogador.left = 0
    if jogador.right > WIDTH:
        jogador.right = WIDTH
    if jogador.top < 0:
        jogador.top = 0
    if jogador.bottom > HEIGHT:
        jogador.bottom = HEIGHT

    for l in lasers[:]:
        l.y -= 10
        if l.y < -20: lasers.remove(l)

    for inimigo in asteroides + ovnis:
        inimigo.x += inimigo.velocidade_x * velocidade_inimigo_atual
        inimigo.y += inimigo.velocidade_y * velocidade_inimigo_atual
        
        if inimigo.left < 0:
            inimigo.left = 0
            inimigo.velocidade_x *= -1
        elif inimigo.right > WIDTH:
            inimigo.right = WIDTH
            inimigo.velocidade_x *= -1
            
        if inimigo.y > HEIGHT + 50:
            jogador.vida -= 1
            sounds.explosao.play()
            if inimigo in asteroides:
                asteroides.remove(inimigo)
            elif inimigo in ovnis:
                ovnis.remove(inimigo)

    for c in coracoes[:]:
        c.y += c.velocidade_y
        if c.y > HEIGHT + 30: coracoes.remove(c)

    pontos_vitoria = NIVEIS[nivel_selecionado]["pontos_para_vencer"]
    if not modo_final_ativado and pontuacao >= pontos_vitoria * 0.80:
        modo_final_ativado = True

    now = time.time()
    if now - last_spawn_time > intervalo_spawn_inimigos:
        last_spawn_time = now
        num_spawn = 1 if not modo_final_ativado else random.randint(1, 3)
        for _ in range(num_spawn): spawn_inimigo()

    if nivel_selecionado in [2, 3] and jogador.vida < MAX_VIDAS:
        if now - last_spawn_time_coracao > INTERVALO_FIXO_SPAWN_CORACAO:
            last_spawn_time_coracao = now
            spawn_coracao()

    for l in lasers[:]:
        for grupo in [asteroides, ovnis]:
            for inimigo in grupo[:]:
                if l.colliderect(inimigo) and l in lasers:
                    pontuacao += inimigo.pontos
                    grupo.remove(inimigo)
                    lasers.remove(l)
                    sounds.explosao.play()

    for grupo in [asteroides, ovnis]:
        for inimigo in grupo[:]:
            if jogador.colliderect(inimigo):
                jogador.vida -= 1
                grupo.remove(inimigo)
                sounds.explosao.play()

    for c in coracoes[:]:
        if jogador.colliderect(c):
            if jogador.vida < MAX_VIDAS:
                jogador.vida += 1
                sounds.vida_extra.play()
            coracoes.remove(c)

    if jogador.vida <= 0 and estado_jogo == ESTADO_JOGANDO:
        estado_jogo = ESTADO_GAME_OVER
        if not som_tocado_game_over:
            sounds.gameover.play()
            som_tocado_game_over = True
    elif pontuacao >= NIVEIS[nivel_selecionado]["pontos_para_vencer"]:
        estado_jogo = ESTADO_VITORIA
        if not som_tocado_vitoria:
            sounds.vitoria.play()
            som_tocado_vitoria = True

def on_key_down(key):
    global estado_jogo
    if estado_jogo == ESTADO_JOGANDO and jogador:
        if key == keys.SPACE:
            now = time.time()
            if now - jogador.last_shot > jogador.shoot_delay:
                jogador.last_shot = now
                laser = AtorRedimensionado('laser', scale=0.2)
                laser.x = jogador.x
                laser.y = jogador.y - 30
                lasers.append(laser)
                sounds.laser.play()
        elif key == keys.P:
            estado_jogo = ESTADO_PAUSADO

    if key == keys.ESCAPE:
        estado_jogo = ESTADO_TELA_INICIAL

def on_mouse_down(pos):
    global estado_jogo, nivel_selecionado
    
    if estado_jogo == ESTADO_TELA_INICIAL:
        if Rect(WIDTH//2 - 100, 300, 200, 60).collidepoint(pos): 
            estado_jogo = ESTADO_ESCOLHA_NIVEL
        if Rect(WIDTH//2 - 100, 400, 200, 60).collidepoint(pos): 
            estado_jogo = ESTADO_TELA_MANUAL
    
    elif estado_jogo == ESTADO_TELA_MANUAL:
        if Rect(WIDTH//2 - 100, 500, 200, 60).collidepoint(pos): 
            estado_jogo = ESTADO_TELA_INICIAL
    
    elif estado_jogo == ESTADO_ESCOLHA_NIVEL:
        largura_btn, altura_btn, espacamento, base_y = 180, 60, 20, 200
        pos_x = WIDTH // 2 - largura_btn // 2
        if Rect(pos_x, base_y, largura_btn, altura_btn).collidepoint(pos):
            nivel_selecionado = 1
            reiniciar_jogo()
            estado_jogo = ESTADO_JOGANDO
        elif Rect(pos_x, base_y + altura_btn + espacamento, largura_btn, altura_btn).collidepoint(pos):
            nivel_selecionado = 2
            reiniciar_jogo()
            estado_jogo = ESTADO_JOGANDO
        elif Rect(pos_x, base_y + 2*(altura_btn + espacamento), largura_btn, altura_btn).collidepoint(pos):
            nivel_selecionado = 3
            reiniciar_jogo()
            estado_jogo = ESTADO_JOGANDO
        elif Rect(pos_x, base_y + 3*(altura_btn + espacamento) + 20, largura_btn, altura_btn).collidepoint(pos):
            estado_jogo = ESTADO_TELA_INICIAL
            
    elif estado_jogo == ESTADO_PAUSADO:
        if Rect(WIDTH//2 - 100, HEIGHT//2 - 20, 200, 60).collidepoint(pos): 
            estado_jogo = ESTADO_JOGANDO
        if Rect(WIDTH//2 - 100, HEIGHT//2 + 60, 200, 60).collidepoint(pos): 
            estado_jogo = ESTADO_TELA_INICIAL
            
    elif estado_jogo == ESTADO_GAME_OVER:
        if Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 200, 60).collidepoint(pos): 
            reiniciar_jogo()
            estado_jogo = ESTADO_JOGANDO
        if Rect(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 60).collidepoint(pos): 
            estado_jogo = ESTADO_TELA_INICIAL
            
    elif estado_jogo == ESTADO_VITORIA:
        if Rect(WIDTH//2 - 125, HEIGHT//2 + 70, 250, 60).collidepoint(pos): 
            reiniciar_jogo()
            estado_jogo = ESTADO_JOGANDO
        if Rect(WIDTH//2 - 125, HEIGHT//2 + 150, 250, 60).collidepoint(pos): 
            estado_jogo = ESTADO_TELA_INICIAL

reiniciar_jogo()
estado_jogo = ESTADO_TELA_INICIAL
pgzrun.go()
