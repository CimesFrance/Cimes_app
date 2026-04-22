import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
from tkinter import PhotoImage
import numpy as np
import os

class AppState():
    """Classe qui contient les variables partagés"""
    def __init__(self):
        self.img_path = ''
        self.mesures = []
        self.choix_mesure = tk.IntVar(value=0)
        self.lire_f_convers() # lire a valeur du facteur conversion contenu dans le fichier.txt
        self.distance_saisie = tk.StringVar(value="0.00")
        self.masque_affichage = [tk.IntVar(value=0) for _ in range(4)]
        self.img_flag = 0 #1 pour une image affichée et 0 sinon
    
    def lire_f_convers(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        camera_params_path = os.path.join(current_dir, "var_prtg.txt")
        with open(camera_params_path) as f:
            line = f.readline().strip() #f.readline() lie une seul ligne jusqu'au "\n", .strip() enlève espace et retour à la ligne
            key, value = line.split("=") #.split("=") sépare la chaine de caractère par le "="
            key, value = key.strip(), value.strip()# on rajoute le .strip() pour se débarasser des espaceements s'ils existent
        self.facteur_conversion = float(value)

        
class image():
    def __init__(self):
        self.id_img = None #Reference de l'image affichée 
        self.tk_img = None #Reference du format Tkinter de l'image importée
        self.coord_origine = [0,0] #Coordonnées de l'origine de l'image
        self.Image_img = None #Reference de l'image importé (sans modifs)

    

class point():
    def __init__(self,num_mesure):
        colors = ['green','red','blue','yellow']
        self.color = colors[num_mesure]
        self.num_mesure = num_mesure
        self.coord_pt_img = [0,0] # Les coordonnées du point sont selon l'image d'origine
        self.coord_pt_canvas = [0,0]
        self.taille = 5 # diamètre du point
        self.id = None
        self.created = False

class ligne():
    def __init__(self,num_mesure):
        colors = ['green','red','blue','yellow']
        self.color = colors[num_mesure]
        self.coord = [0,0,0,0] #format x1,y1,x2,y2
        self.id = None
        self.created = False

class fenetre_image(tk.Canvas):
    def __init__(self,parent,var_partg,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        self.img = image()
        self.deb_deplc_img = []
        self.deb_deplc_pt = []
        self.pt_select = -1
        self.zoom_factor = 1
        self.points = []
        self.var_partg = var_partg
        self.mouvement_pt = 0

        self.bind("<ButtonPress-3>",self._deplacement)
        self.bind("<B3-Motion>", self._deplacement)
        self.bind("<MouseWheel>", self._zoom)
        self.bind("<ButtonPress-1>", self._handl_pt)
        self.bind("<B1-Motion>", self._handl_pt)


    def load_img(self,path):
        self.img.Image_img = Image.open(path)
        self.img.coord_origine = [0,0]
        self.var_partg.img_flag = 1
        self._maj_fenetre()
    
    def afficher_mesure(self):
        return None
    
    def _deplacement(self,event):
        if event.type == "4": #event.type vaut "4" si le bouton vient d'être pressé, c'est equivalent au start de déplacement (<ButtonPress-3>)
            self.deb_deplc_img = [event.x,event.y]
        if event.type ==  "6":#event.type vaut "6" si le bouton est pressé, c'est equivalent de déplacement(<B3-Motion>)
            dx , dy = event.x - self.deb_deplc_img[0] , event.y - self.deb_deplc_img[1]
            self.img.coord_origine = [self.img.coord_origine[0] + dx , self.img.coord_origine[1] + dy]
            self.deb_deplc_img = [event.x,event.y] #On met à jour le début de déplacement
            self._maj_fenetre() # On met à jour la fenêtre uniquement dans le cas de déplacement pas de début
    
    def _zoom(self,event):
        zoom_prec = self.zoom_factor
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else :
            self.zoom_factor *= 0.9
        factor_anc_nv = self.zoom_factor / zoom_prec
        coord_cible_img = [(event.x - self.img.coord_origine[0]) * factor_anc_nv, 
                           (event.y - self.img.coord_origine[1]) * factor_anc_nv]
        dx_dy = [coord_cible_img[0] + self.img.coord_origine[0] - event.x,
                 coord_cible_img[1] + self.img.coord_origine[1] - event.y]
        self.img.coord_origine = [self.img.coord_origine[0] - dx_dy[0],
                                  self.img.coord_origine[1] - dx_dy[1]]
        self._maj_fenetre()

    def _maj_fenetre(self):
        image = self.img.Image_img
        new_w = int(image.width * self.zoom_factor)
        new_h = int(image.height * self.zoom_factor)
        image = image.resize((new_w, new_h), Image.LANCZOS)
        self.img.tk_image  = ImageTk.PhotoImage(image)
        self.delete('all')
        self.create_image(self.img.coord_origine[0],self.img.coord_origine[1],anchor="nw",image=self.img.tk_image)
        for i,mesure in enumerate(self.var_partg.mesures):
            coord_ligne_canvas = []
            if mesure.flag_affiche.get():
                for j,pt in enumerate(mesure.pts):
                    if pt.created == True :
                        x = (pt.coord_pt_img[0] *  self.zoom_factor) + self.img.coord_origine[0]
                        y = (pt.coord_pt_img[1] * self.zoom_factor) + self.img.coord_origine[1]
                        self.var_partg.mesures[i].pts[j].coord_pt_canvas = [x,y]
                        coord_ligne_canvas.extend([x,y])
                        self.create_oval(x-5, y-5, x+5, y+5, fill=pt.color)
                if mesure.pts[1].created == True:
                    vect_longueure = [mesure.pts[0].coord_pt_img[0] - mesure.pts[1].coord_pt_img[0],
                                      mesure.pts[0].coord_pt_img[1] - mesure.pts[1].coord_pt_img[1]]
                    str_l_ligne = str(round(np.sqrt(vect_longueure[0]**2+vect_longueure[1]**2) * self.var_partg.facteur_conversion,2))
                    self.var_partg.mesures[i].distance_calcule.set(str_l_ligne)
                    self.create_line(coord_ligne_canvas[0], coord_ligne_canvas[1], coord_ligne_canvas[2], coord_ligne_canvas[3], fill=mesure.pts[1].color, width=2)

        
    def _handl_pt(self,event):
        if self.var_partg.mesures[self.var_partg.choix_mesure.get()].created == 1 and self.var_partg.img_flag and self.clic_on_img([event.x,event.y]):
            if event.type == "4" : #(<ButtonPress-1>)
                pt_appuye = False
                for i,pt in enumerate(self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts):
                    if pt.created :
                        if self.pt_selectionne([event.x,event.y],pt):
                            pt_appuye = True
                            self.pt_select = i
                            break
                if not pt_appuye:
                    if self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[0].created and self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[1].created :
                        self.mouvement_pt = 0
                    x = (event.x - self.img.coord_origine[0]) / self.zoom_factor
                    y = (event.y - self.img.coord_origine[1]) / self.zoom_factor
                    for i,point in enumerate(self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts):
                        if not point.created :
                            self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[i].coord_pt_img = [x,y]
                            self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[i].created = True
                            self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[i].coord_pt_canvas = [event.x,event.y]
                            break
                else :
                    self.deb_deplc_pt = [event.x,event.y]
                    self.mouvement_pt = 1
                self._maj_fenetre()
            if event.type == "6" and self.mouvement_pt: #<B1-Motion>
                dx , dy = event.x - self.deb_deplc_pt[0] , event.y - self.deb_deplc_pt[1]
                dx_img , dy_img = dx / self.zoom_factor , dy / self.zoom_factor
                coord_pt_act = self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[self.pt_select].coord_pt_img
                coord_pt = [coord_pt_act[0] + dx_img , coord_pt_act[1] + dy_img]
                self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[self.pt_select].coord_pt_img = coord_pt
                self.var_partg.mesures[self.var_partg.choix_mesure.get()].pts[self.pt_select].coord_pt_canvas = [event.x,event.y]
                self.deb_deplc_pt = [event.x,event.y]
                self._maj_fenetre()
        
    def clic_on_img(self,coord_souris):
        image = self.img.Image_img
        x_good = coord_souris[0] >= (self.img.coord_origine[0]) and coord_souris[0] <= (self.img.coord_origine[0]+image.width*self.zoom_factor)
        y_good = coord_souris[1] >= (self.img.coord_origine[1]) and coord_souris[1] <= (self.img.coord_origine[1]+image.height*self.zoom_factor)
        return x_good and y_good

    @staticmethod 
    def pt_selectionne(coord_souris,pt): # quand on n'utilise pas self, vaut mieux faire ça por eviter les ennuis
        """Fonction qui renvoie True si la cible de la souris est sur le point pt et False sinon"""
        # pt : Objet point
        # coord_souris : List qui contient [event.x,event.y]
        dist = np.sqrt((coord_souris[0] - pt.coord_pt_canvas[0])**2+(coord_souris[1] - pt.coord_pt_canvas[1])**2)
        return dist <= pt.taille

    
class barre_outils(tk.Frame):
    def __init__(self,parent,var_partg,fenetre_img,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        self.var_partg = var_partg
        self.fi = fenetre_img
        btn_ouvrir = ttk.Button(self,text='Ouvrir',command=self._charger_img)
        #Disposition Boutons#
        btn_ouvrir.grid(row=0,column=0,sticky='we',padx=(1,1),pady=(1,1))
        #Organisation barre d'outils
        self.columnconfigure(0,weight=1)

    def _charger_img(self):
        path = filedialog.askopenfilename(title='veilleur selectionner une image')
        if not path:
            print("Erreur : Aucune fichier n'a été selectionné")
        else :
            self.fi.load_img(path)


class une_mesure(tk.Frame):
    def __init__(self,parent,num_mesure,var_partg,fenetre_img,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        colors = ['green','red','blue','yellow']
        self.var_partg = var_partg
        self.distance_calcule = tk.StringVar(value='0.00')
        self.fi = fenetre_img
        self.num_mesure = num_mesure
        self.flag_affiche = tk.IntVar(self,value=0)
        self.state = "normal"
        self.created = 0
        self.pts = [point(num_mesure) , point(num_mesure)]
        self.ligne = ligne(num_mesure)
        title = tk.Label(self,text=f"Mesure N°{num_mesure+1}")
        color_square = tk.Label(self, bg=colors[num_mesure], width=2, height=1, relief="raised")
        self.chek_affichage = tk.Checkbutton(self,text='Afficher',variable=self.flag_affiche
                                        ,command=self.afficher_mesure,onvalue=1, offvalue=0,compound='top')
        self.chek_affichage.config(state="disabled")
        select_mesure = tk.Radiobutton(self,text='Selectionner',value=num_mesure,variable=self.var_partg.choix_mesure)
        self.label_afficheur_longueure = tk.Label(self,text="Longueur mesurée  ",state="disabled")
        self.afficheur_longueure = tk.Label(self,textvariable=self.distance_calcule,state="disabled")
        
        #Disposition elt fenêtre#
        title.grid(row=0,column=0,columnspan=2,sticky='w',padx=(2,2),pady=(2,2))
        color_square.grid(row=0,column=1,sticky='e',padx=(2,2),pady=(2,2))
        self.chek_affichage.grid(row=1,column=0,sticky='w')
        select_mesure.grid(row=1,column=1,sticky="e")
        self.label_afficheur_longueure.grid(row=2,column=0,sticky="w",padx=(2,2),pady=(2,2))
        self.afficheur_longueure.grid(row=2,column=1,sticky='w',padx=(2,2),pady=(2,2))
        #Organisation de la fenêtre#
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)

    def creer_mesure(self):
        self.created = 1
        self.flag_affiche.set(1)
        self.distance_calcule.set("0.00")
        self.chek_affichage.config(state="normal")
        self.label_afficheur_longueure.config(state="normal")
        self.afficheur_longueure.config(state="normal")

    def supprimer_mesure(self):
        self.created = 0
        self.flag_affiche.set(0)
        self.distance_calcule.set("0.00")
        self.pts[0].created = False
        self.pts[1].created = False
        self.ligne.created = False
        self.chek_affichage.config(state="disabled")
        self.label_afficheur_longueure.config(state="disabled")
        self.afficheur_longueure.config(state="disabled")
        self.fi._maj_fenetre()

    def afficher_mesure(self):
        if self.var_partg.img_flag: # On gère l'affichage de mesure uniquement s'il y a une image
            if  self.created == 1:
                self.fi._maj_fenetre()
    
    
class barre_mesure(tk.Frame):
    def __init__(self,parent,var_partg,fenetre_img,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        self.var_partg = var_partg
        self.fi = fenetre_img
        titre = tk.Label(self,text="Mesures",font=("Arial", 14, "bold"))
       
        for i in range(4):
            self.var_partg.mesures.append(une_mesure(self,i,self.var_partg,self.fi))

        btn_ajouter = ttk.Button(self,text="Ajouter",command=self.ajouter_mesure)
        btn_supprimer = ttk.Button(self,text="Supprimer",command=self.supprimer_mesure)
        #Disposition elt fenêtre#
        titre.grid(row=0,column=0,columnspan=10,sticky='we',padx=(2,2),pady=(2,2))
        btn_ajouter.grid(row=1,column=0,sticky="ew",padx=(2,2),pady=(2,2))
        btn_supprimer.grid(row=1,column=1,sticky="ew",padx=(2,2),pady=(2,2))
        for i,measures in enumerate(self.var_partg.mesures):
            measures.grid(row=i+2,column=0,columnspan=2,sticky='nwe',padx=(2,2),pady=(2,2))
        #Organisation de la fenêtre#
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        for i in range(2,6):
            self.rowconfigure(i,weight=1)
    
    def ajouter_mesure(self):
        self.var_partg.mesures[self.var_partg.choix_mesure.get()].creer_mesure()

    def supprimer_mesure(self):
        self.var_partg.mesures[self.var_partg.choix_mesure.get()].supprimer_mesure()

class barre_conversion(tk.Frame):
    def __init__(self,parent,var_partg,fenetre_img,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        self.var_partg = var_partg
        self.fi = fenetre_img
        titre = tk.Label(self,text="Changement d'échelle",font=("Arial", 14, "bold"))
        label_choix_mesure = tk.Label(self,text="Mesure")
        choix_bouttons = []
        for i in range(4):
            tk_button = tk.Radiobutton(self,text=str(i+1),value=i,variable=self.var_partg.choix_mesure)
            choix_bouttons.append(tk_button)
        label_mesure_mm = tk.Label(self,text='Longueur réelle')
        espace_distance_saisie = tk.Entry(self,textvariable=self.var_partg.distance_saisie)
        btn_confirmer = tk.Button(self,text='Changer échelle',command=self._changer_echelle)

        #Disposition elt fenêtre#
        titre.grid(row=0,column=0,columnspan=6,sticky='we',padx=(2,2),pady=(2,2))
        label_choix_mesure.grid(row=1,column=0,sticky='w',padx=(2,2),pady=(2,2))
        for i in range(1,5):
            choix_bouttons[i-1].grid(row=1,column=i,padx=(1,1),pady=(1,1))
            choix_bouttons[i-1].config(state="disabled") #Sans mesure on ne peux rien choisir
        label_mesure_mm.grid(row=2,column=0,sticky='w',padx=(2,2),pady=(2,2))
        espace_distance_saisie.grid(row=2,column=1,columnspan=6,sticky='e',padx=(2,2),pady=(2,2))
        btn_confirmer.grid(row=3,column=0,columnspan=6,sticky='we',padx=(2,2),pady=(2,2))
        #Organisation de la fenêtre#
        self.columnconfigure(0,weight=6)

    def _changer_echelle(self):
        self.win=tk.Toplevel(self)
        self.win.title("Attention")
        self.win.geometry("400x80")
        self.win.grab_set()
        message = tk.Label(self.win,text=f"Confirmer que vous voulez changer l'echelle selon la mesure N°{self.var_partg.choix_mesure.get()+1} ?")
        btn_oui = tk.Button(self.win,text="Oui",command=self.rep_confirmation_oui)
        btn_non = tk.Button(self.win,text="Non",command=self.rep_confirmation_non)
        message.grid(row=0,column=0,columnspan=2,padx=(2,2),pady=(10,2))
        btn_oui.grid(row=1,column=0,sticky="we",padx=(2,2),pady=(10,2))
        btn_non.grid(row=1,column=1,sticky='we',padx=(2,2),pady=(10,2))

    
    def rep_confirmation_oui(self):
        if self.var_partg.facteur_conversion == 0:
            print("Error : Division par 0 !")
            self.win.destroy()
            return None
        else:
            distance_pixel = float(self.var_partg.mesures[self.var_partg.choix_mesure.get()].distance_calcule.get()) / self.var_partg.facteur_conversion
        if distance_pixel == 0:
            print("Error : Division par 0 !")
            self.win.destroy()
            return None
        else :
            self.var_partg.facteur_conversion = float(self.var_partg.distance_saisie.get()) / distance_pixel
            current_dir = os.path.dirname(os.path.abspath(__file__))
            camera_params_path = os.path.join(current_dir, "var_prtg.txt")
            with open(camera_params_path, "w") as ch_carac:# ouvrir le fichier avec "w" c'est supprimer tout son contenue
                ch_carac.write(f"facteur_conversion = {round(self.var_partg.facteur_conversion,2)}") #mettre à jour le coeff de conversion
            self.fi._maj_fenetre()
            self.win.destroy()
        return None

    def rep_confirmation_non(self):
        self.win.destroy()
        return None

class Application_calibrage(tk.Toplevel): # pour l'utiliser individuellement il faut changer Application_calibrage(tk.Tk)
    def __init__(self):
        super().__init__()
        self.title("Calibrage de camera")
        self.geometry("1100x700")
        self.resizable(False,False)
        var_partg = AppState()
        fi = fenetre_image(self,var_partg)
        bo = barre_outils(self,var_partg,fi,height=50,bg="grey")
        bm = barre_mesure(self,var_partg,fi,width=300,height=500,bg='grey')
        bc = barre_conversion(self,var_partg,fi,width=300,height=130,bg='grey')

        #Disposition elt fenêtre#
        fi.grid(row=1,column=0,rowspan=2,sticky="nsew",padx=(1,1),pady=(1,1))
        bo.grid(row=0,columnspan=2,sticky='we',padx=(1,1),pady=(1,1))
        bm.grid(row=1,column=1,sticky="nsew",padx=(1,1),pady=(1,1))
        bm.grid_propagate(False)
        bc.grid(row=2,column=1,sticky="nsew",padx=(1,1),pady=(1,1))
        bc.grid_propagate(False)
        #Organisation de la fenêtre#
        self.rowconfigure(0,weight=0)
        self.rowconfigure(1,weight=1)
        self.columnconfigure(0,weight=1)
        

# if __name__ == '__main__':
#   app = Application_calibrage()
#   app.mainloop()

