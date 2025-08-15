################################
###### Visualización con R######
##### Prof. David Zavaleta######
################################

setwd("D:/RFolder/")

rm(list=ls())

#install.packages("tidyverse")
#install.packages("reshape2")
library(tidyverse)
#library(reshape2)

#Datos del Social Security Administration US

death <- read_csv("https://www.tylermw.com/data/death.csv", skip=1)
death2 <- death %>% 
  pivot_longer(2:121, names_to="edad", values_to = "probabilidad")

#death2 <- reshape2::melt(death, id.vars="Year")

death2$edad <- as.numeric(as.character(death2$edad))

#death2 <- death2 %>% 
#  rename(edad=variable, probabilidad=value)

# para el año 1900

datos1900 <- death2 %>% 
  filter(Year==1900)

ggp1900 <- ggplot(datos1900, aes(x=edad, y=probabilidad))+
  geom_point(size=1, color="red")

plot(ggp1900)

# para el año 1950

datos1950 <- death2 %>% 
  filter(Year==1950)

ggp1950 <- ggplot(datos1950, aes(x=edad, y=probabilidad))+
  geom_point(size=1, color="red")

plot(ggp1950)

# para el año 2000

datos2000 <- death2 %>% 
  filter(Year==2000)

ggp2000 <- ggplot(datos2000, aes(x=edad, y=probabilidad))+
  geom_point(size=1, color="red")

plot(ggp2000)

#para los 3 años

datos190019502000 <- death2 %>% 
  filter(Year == 1900 | Year==1950 | Year==2000)

ggp190019502000 <- ggplot(datos190019502000, aes(x=edad, y=probabilidad))+
  geom_point(aes(color=factor(Year)))

ggp190019502000

#otra manera

ggp3alt <- ggplot(datos190019502000, aes(edad,probabilidad))+
  geom_point()+
  facet_wrap(~Year)

ggp3alt

#themes
install.packages("ggthemes")
library(ggthemes)

ggp3alt <- ggplot(datos190019502000, aes(edad,probabilidad))+
  geom_point()+
  facet_wrap(~Year)+
  theme_economist()

ggp3alt

#alternativa dinámica

install.packages("gganimate")
install.packages("gifski")
library(gganimate)
library(gifski)

ggp3anim <- ggplot(death2, aes(edad, probabilidad))+
  geom_point(aes(color=factor(Year)))+
  theme(legend.position = "none")+
  labs(title='Año:{frame_time}')+
  transition_time(Year)
ggp3anim

animate(ggp3anim, nframes=111,
        render=gifski_renderer("prueba.gif"))
