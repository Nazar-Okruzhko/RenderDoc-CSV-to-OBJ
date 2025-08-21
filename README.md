# RenderDoc "CSV-2-OBJ" converter
<img width="890" height="706" alt="Screenshot (3108)" src="https://github.com/user-attachments/assets/345dd92b-948a-4055-9a2c-eef25ae74391" />

# Usage & Workarounds 

Drag and drop Single/Multiple .CSV files into the tool, this will automatically generate .OBJ files which will require a bit of workaround later in Blender.

<img width="776" height="427" alt="Screenshot (3097)" src="https://github.com/user-attachments/assets/856ad3c2-be4a-49a7-8308-f20ec4ac7f9a" />

But remember that not all .CSV files have always same column structure, (Vertex position & UV map colums).
The program has the default RenderDoc's structure by default, you can of course easily cutomize this by adjusting the column orders of Vertex position & UV map colums to correspond to your .CSV file

<img width="555" height="486" alt="Screenshot (3111)" src="https://github.com/user-attachments/assets/f6d752a0-a247-42c1-ac6c-3492f88022b7" />

After converting all the .CSV files into OBJ format in Blender Select All by pressing 'A' and Merge (By Distance) by pressing 'M' (in Edit Mode).

<img width="514" height="373" alt="Screenshot (3104)" src="https://github.com/user-attachments/assets/e8402fe6-fba5-4753-8b23-890eb98a8c38" />

Don't forget to Shde Smooth the model (Right mouse button in Object mode).

<img width="550" height="402" alt="Screenshot (3106)" src="https://github.com/user-attachments/assets/7558ef2d-8d04-40e6-9ec9-e082a133fe01" />


The final result in terms of this model will look exactly like in the first image but of course this applies to all the models in .CSV format.
