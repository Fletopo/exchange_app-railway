import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, MessageMedia
from users.models import CustomUser
from publication.models import Contrato
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
import base64
from django.core.files.base import ContentFile
from django.db.models import Q
from publication.serializer import UserSerializer
from django.forms.models import model_to_dict
import asyncio
from datetime import datetime, timedelta

active_publish = {}
active_contracts = {}
active_timers = {}
active_users = {}
chat_messages = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            raise DenyConnection("Usuario no autenticado")

        # Usamos los IDs de los usuarios para crear un identificador único de la conversación
        self.sender = self.scope["user"]
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']  # ID del receptor en la URL
        try:
            self.receiver = await CustomUser.objects.aget(id=self.receiver_id)
        except CustomUser.DoesNotExist:
            await self.close()
            return
        
        # Creamos un identificador único para la conversación
        self.chat_id = self.get_chat_id(self.sender.id, self.receiver.id)

        # Añadimos al consumidor al canal único basado en los dos usuarios
        await self.channel_layer.group_add(
            self.chat_id,
            self.channel_name
        )

        await self.accept()

        # Obtener los mensajes existentes entre el emisor y el receptor
        messages = await database_sync_to_async(self.get_messages)(self.sender, self.receiver)

        # Enviar los mensajes existentes al cliente que se conecta
        await self.send(text_data=json.dumps({
            'type': 'initial_messages',
            'messages': messages
        }))

        publish = active_publish.get(self.chat_id)
        if publish:
            await self.send(text_data=json.dumps({
                'type':'existing_publish',
                'publish':publish,
            }))

        contract = active_contracts.get(self.chat_id)
        if contract:
            await self.send(text_data=json.dumps({
                'type':'existing_contract',
                'contract':contract,
            }))

    async def disconnect(self, close_code):
        # Eliminamos al consumidor del canal de conversación
        await self.channel_layer.group_discard(
            self.chat_id,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')

        if event_type == "button_pressed":
            await self.handle_button_press(data)
        elif event_type == "chat_message":
            await self.handle_chat_message(data)
        elif event_type == 'new_contract':
            await self.handle_new_contract(data)
        elif event_type == 'new_publish':
            await self.handle_new_publish(data)
        elif event_type == 'reset_contract':
            await self.handle_reset_contract(data)
        elif event_type == 'reset_publish':
            await self.handle_reset_publish(data)
        elif event_type == 'rating':
            await self.handle_get_datar(data)

    async def handle_get_datar(self, data):
        contract = active_contracts.get(self.chat_id)
        publish = active_publish.get(self.chat_id)

        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'broadcast_get_datar',
                'contract': contract,
                'publish': publish,
            }
        )

    async def broadcast_get_datar(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'type':'rating',
                    'contract': event.get('contract'),
                    'publish': event.get('publish'),
                }
            )
        )

    async def handle_reset_publish(self, data):
        if self.chat_id in active_publish:
            del active_publish[self.chat_id]

        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'broadcast_reset_publish'
            }
        )

    async def broadcast_reset_publish(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'type':'reset_publish',
                }
            )
        )

    async def handle_reset_contract(self, data):
        if self.chat_id in active_contracts:
            del active_contracts[self.chat_id]

        # Cancelar el temporizador si existe
        if self.chat_id in active_timers:
            active_timers[self.chat_id].cancel()
            del active_timers[self.chat_id]

        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'broadcast_reset_contract'
            }
        )

    async def broadcast_reset_contract(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'type':'reset_contract',
                }
            )
        )

    async def handle_new_publish(self, data):
        publish = data.get('publish')
        if not publish:
            print("Error: No se recibió información de la publicación")
            return

        active_publish[self.chat_id] = publish

        # Notificar a los participantes del nuevo publish
        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'broadcast_new_publish',
                'publish': publish,
            }
        )

        # Crear un mensaje predeterminado automáticamente
        default_message = "Estoy interesado en esta publicación :)"
        new_message = await database_sync_to_async(Message.objects.create)(
            sender=self.sender,
            receiver=self.receiver,
            content=default_message
        )

        # Reiniciar la lista de mensajes del chat para la nueva publicación
        chat_messages[self.chat_id] = {'user_r': [], 'user_p': []}

        # Añadir el mensaje a la lista de mensajes del chat
        if self.chat_id not in chat_messages:
            chat_messages[self.chat_id] = {'user_r': [], 'user_p': []}

        chat_messages[self.chat_id]['user_r'].append({
            'id': new_message.id,
            'message': default_message,
            'timestamp': new_message.timestamp.isoformat()
        })

        # Limitar la lista a 3 mensajes por cada usuario
        if len(chat_messages[self.chat_id]['user_r']) > 3:
            chat_messages[self.chat_id]['user_r'].pop(0)

        # Enviar el mensaje predeterminado al chat
        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'chat_message',
                'message': default_message,
                'id': new_message.id,
                'media': [],
                'sender': UserSerializer(self.sender).data,
                'receiver': UserSerializer(self.receiver).data,
                'timestamp': new_message.timestamp.isoformat(),
            }
        )

        if self.chat_id in active_users:
            del active_users[self.chat_id]


    async def broadcast_new_publish(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_publish',
            'publish': event['publish'],
        }))

    async def handle_new_contract(self, data):
        contract = data.get('contract')
        meeting_date = contract.get('meeting_date')
        duration = data.get('duration', 10)
        chat_messages[self.chat_id] = {'user_r': [], 'user_p': []}
        
        if not contract:
            print("Error: No se recibió información del contrato")
            return
        
        meeting_date = contract.get('meeting_date')
        if self.chat_id in active_contracts:
            existing_contract = active_contracts[self.chat_id]
            if existing_contract['id'] == contract['id']:
                print("Contrato ya existente, no se sobrescribe")
                return

        # Si meeting_date está presente, intentar convertirlo
        if meeting_date:
            print(f"Fecha recibida: {meeting_date}")
            try:
                # Eliminar 'Z' de la fecha si está presente para poder usar fromisoformat
                if meeting_date.endswith('Z'):
                    meeting_date = meeting_date[:-1]  # Elimina la 'Z' al final de la fecha

                # Intentar analizar la fecha en formato ISO 8601
                meeting_datetime = datetime.fromisoformat(meeting_date)
                now = datetime.now()
                duration = (meeting_datetime - now).total_seconds()
                if duration <= 0:
                    print("Error: La fecha de reunión ya ha pasado")
                    return
            except ValueError:
                print("Error: Formato de fecha inválido en `meeting_date`")
                return

        active_contracts[self.chat_id] = contract
        
        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'broadcast_new_contract',
                'contract': contract,
            }
        )

        if active_timers.get(self.chat_id):
            active_timers[self.chat_id].cancel()

        timer_task = asyncio.create_task(self.contract_timer(self.chat_id, duration))
        active_timers[self.chat_id] = timer_task

        if self.chat_id in active_users:
            del active_users[self.chat_id]



    async def contract_timer(self, chat_id, duration):
        """Cancela automáticamente el contrato después del tiempo límite."""
        print(f"Iniciando temporizador para chat_id: {chat_id} durante {duration} segundos")
        try:
            await asyncio.sleep(duration)  # Espera el tiempo especificado
            print(f"Tiempo cumplido para chat_id: {chat_id}")
            if chat_id in active_contracts:
                print(f"Eliminando contrato activo para chat_id: {chat_id}")
                contract = active_contracts[chat_id]
                try:
                    time = datetime.now() + timedelta(days=1)
                    time_serialized = time.isoformat()
                    # Verifica si contract es un diccionario y maneja los datos correctamente
                    if isinstance(contract, dict):
                        # Obtiene la instancia del contrato y actualiza su estado
                        contract_instance = await database_sync_to_async(self.get_contract_instance)(contract['id'])
                        contract_instance.contract_state = 'Cancelado'
                        await database_sync_to_async(contract_instance.save)()

                        # Obtiene la instancia del usuario y actualiza su estado
                        user_instance = await database_sync_to_async(self.get_user_instance)(contract['user_r'])
                        user_instance.can_trade = False
                        user_instance.cant_trade_time = datetime.now() + timedelta(days=1)  # Baneo por 1 día
                        await database_sync_to_async(user_instance.save)()

                    else:
                        # Manejo si contract ya es un objeto
                        contract.contract_state = 'Cancelado'
                        await database_sync_to_async(contract.save)()

                        user_instance = await database_sync_to_async(self.get_user_instance)(contract.user_r)
                        user_instance.can_trade = False
                        user_instance.cant_trade_time = datetime.now() + timedelta(days=1)
                        
                        await database_sync_to_async(user_instance.save)()
                        
                except Exception as e:
                    print(f"Error al actualizar estado del contrato o usuario: {e}")

                del active_contracts[chat_id]
                del active_publish[chat_id]
                del active_timers[chat_id]
                # Notifica a los participantes
                await self.channel_layer.group_send(
                    chat_id,
                    {
                        'type': 'broadcast_contract_timeout',
                        'contract':contract,
                        'time': time_serialized
                    }
                )
                print(f"Contrato {contract} eliminado y notificación enviada")
            else:
                print(f"No se encontró un contrato activo para chat_id: {chat_id}")
        except asyncio.CancelledError:
            print(f"Temporizador cancelado para chat_id: {chat_id}")

    def get_user_instance(self, user_r):
        """Obtiene la instancia de CustomUser a partir del id."""
        try:
            return CustomUser.objects.get(id=user_r['id'])
        except CustomUser.DoesNotExist:
            raise Exception('Usuario no encontrado')

    def get_contract_instance(self, contract_id):
        """Obtiene la instancia del contrato a partir de su id."""
        try:
            return Contrato.objects.get(id=contract_id)
        except Contrato.DoesNotExist:
            raise Exception("Contrato no encontrado")


    async def broadcast_contract_timeout(self, event):
        """Envía una notificación a los clientes cuando expira el contrato."""
        await self.send(text_data=json.dumps({
            'type': 'contract_timeout',
            'message': 'El contrato ha expirado automáticamente.',
            'contract': event['contract'],
            'time':event['time']
        }))

    async def broadcast_new_contract(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_contract',
            'contract': event['contract'],
        }))

    async def handle_button_press(self, data):
        user_id = data.get('user_id')
        if not user_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'User ID is required.'
            }))
            return

        # Inicializar la lista de usuarios para este chat si no existe
        if self.chat_id not in active_users:
            active_users[self.chat_id] = []

        # Agregar el usuario a la lista si no está ya presente
        if user_id not in active_users[self.chat_id]:
            active_users[self.chat_id].append(user_id)

        # Enviar notificación del botón presionado
        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'broadcast_button_press',
                'user_id': user_id,
            }
        )

        # Si ambos usuarios han presionado el botón
        if len(active_users[self.chat_id]) == 2:
            # Obtener la lista de usuarios
            users_pressed = active_users[self.chat_id]

            # Notificar al frontend que ambos usuarios han presionado el botón
            await self.channel_layer.group_send(
                self.chat_id,
                {
                    'type': 'broadcast_both_pressed',
                    'users': users_pressed,
                }
            )

            
    async def broadcast_button_press(self, event):
        await self.send(text_data=json.dumps({
            'type': 'button_pressed',
            'user_id': event['user_id'],
        }))

    async def broadcast_both_pressed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'both_buttons_pressed',
            'users': event['users'],
        }))

    # Manejar el mensaje enviado (con imágenes y videos)
    # Manejar el mensaje enviado (con imágenes y videos)
    async def handle_chat_message(self, data):
        message = data.get('content', '')
        media_files = data.get('media', [])
        sender_id = data.get('sender')

        try:
            sender = await CustomUser.objects.aget(id=sender_id)
        except CustomUser.DoesNotExist:
            await self.close()
            return

        sender_data = UserSerializer(sender).data

        # Crear el mensaje en la base de datos
        new_message = await database_sync_to_async(Message.objects.create)(
            sender=sender,
            receiver=self.receiver,
            content=message
        )

        # Verifica e inicializa la clave para chat_id
        if self.chat_id not in chat_messages:
            chat_messages[self.chat_id] = {'user_r': [], 'user_p': []}

        # Usar active_publish para validar si el sender es el correcto
        if self.chat_id in active_publish:
            active_contract = active_publish[self.chat_id]

            if isinstance(active_contract['user'], dict):
                user_id = active_contract['user'].get('id')
            else:
                user_id = active_contract['user'].id

            # Verificar si el sender es el que corresponde al contrato/publicación activa
            if sender.id != user_id:
                # El mensaje es enviado por el usuario que corresponde al contrato
                chat_messages[self.chat_id]['user_r'].append({
                    'id': new_message.id,
                    'message': new_message.content,
                    'timestamp': new_message.timestamp.isoformat()
                })
                # Limitar a 3 mensajes por user_r
                if len(chat_messages[self.chat_id]['user_r']) > 3:
                    chat_messages[self.chat_id]['user_r'].pop(0)
            else:
                # El mensaje no es del usuario correspondiente al contrato activo
                chat_messages[self.chat_id]['user_p'].append({
                    'id': new_message.id,
                    'message': new_message.content,
                    'timestamp': new_message.timestamp.isoformat()
                })
                # Limitar a 3 mensajes por user_p
                if len(chat_messages[self.chat_id]['user_p']) > 3:
                    chat_messages[self.chat_id]['user_p'].pop(0)
        else:
            # No hay publicación activa para este chat_id
            print(f"No se encontró una publicación activa para el chat_id: {self.chat_id}")

        # Comprobar si se han alcanzado 6 mensajes en total
        total_messages = len(chat_messages[self.chat_id]['user_r']) + len(chat_messages[self.chat_id]['user_p'])
        if total_messages >= 6:
            # Actualizar el estado en la base de datos
            await self.update_message_status(new_message)

        # Procesar los archivos multimedia (imágenes o videos)
        media_list = []
        for media in media_files:
            try:
                base64_data = media.get('base64', '')
                file_name = media.get('name', 'unknown.jpg')
                media_file = ContentFile(base64.b64decode(base64_data), name=file_name)

                # Crear el objeto Media asociado al mensaje
                new_media = await database_sync_to_async(MessageMedia.objects.create)(
                    message=new_message,
                    media=media_file
                )

                media_list.append({
                    'id': new_media.id,
                    'url': new_media.media.url,
                    'type': new_media.get_media_type(),
                })
            except Exception as e:
                print(f"Error procesando archivo multimedia: {e}")

        # Serializar el receptor
        receiver_data = UserSerializer(self.receiver).data

        # Enviar el mensaje a todos los participantes de la conversación
        await self.channel_layer.group_send(
            self.chat_id,
            {
                'type': 'chat_message',
                'message': message,
                'id': new_message.id,
                'media': media_list,
                'sender': sender_data,
                'sender_id': sender_id,
                'receiver': receiver_data,
                'timestamp': new_message.timestamp.isoformat(),
            }
        )

    async def update_message_status(self, new_message):
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'message': 'Se ha alcanzado el límite de 6 mensajes.'
        }))

    # Enviar el mensaje al cliente (con medios)
    async def chat_message(self, event):
        content = event.get('message', '')
        media = event.get('media', [])
        message_id = event.get('id')
        sender = event.get('sender')
        sender_id = event.get('sender_id')
        receiver = event.get('receiver')
        timestamp = event.get('timestamp')

        # Enviar el mensaje y los archivos al cliente
        await self.send(text_data=json.dumps({
            'id': message_id,
            'content': content,
            'media': media,
            'sender': sender,
            'sender_id':sender_id,
            'receiver': receiver,
            'timestamp': timestamp,
            'is_read': False
        }))

    def get_chat_id(self, sender_id, receiver_id):
        """Generar un ID único para el chat entre dos usuarios basado en sus IDs"""
        return f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"

    def get_messages(self, sender, receiver):
        """Obtener los mensajes entre el emisor y el receptor"""
        # Usar Q para filtrar por los dos usuarios y ordenarlos por timestamp
        messages = Message.objects.filter(
            Q(sender=sender) & Q(receiver=receiver) |
            Q(sender=receiver) & Q(receiver=sender)
        ).order_by('timestamp')

        # Construir la respuesta para enviar al cliente
        messages_list = []
        for message in messages:
            # Recopilar los medios asociados con el mensaje
            media_files = MessageMedia.objects.filter(message=message)
            media_list = [{
                'id': media.id,
                'url': media.media.url,
                'type': media.get_media_type(),  # 'image' o 'video'
            } for media in media_files]

            messages_list.append({
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_id':message.sender.id,
                'receiver': message.receiver.username,
                'timestamp': message.timestamp.isoformat(),
                'media': media_list,
                'is_read': message.is_read
            })
        return messages_list